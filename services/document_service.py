import os
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status
from config import settings
from database.repository import Repository
from documents.pdf_processor import extract_text_from_pdf
from documents.docx_processor import extract_text_from_docx
from documents.txt_processor import extract_text_from_txt
from rag.chunker import chunk_extracted_pages
from rag.embeddings import get_embeddings_batch
from rag.vector_store import vector_store

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_MB = 20


class DocumentService:
    @staticmethod
    def process_and_store_document(
        db: Session,
        file: UploadFile,
        title: str,
        department: str,
        category: str,
        admin_id: int,
    ):
        # 1. Validate extension
        filename = file.filename or "uploaded_document"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, DOCX, TXT.",
            )

        # 2. Save file to disk
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE_MB}MB.",
            )

        # 3. Create document record in database
        doc = Repository.create_document(
            db=db,
            file_name=filename,
            file_type=ext.replace(".", "").upper(),
            file_path=file_path,
            title=title or filename,
            department=department or "General",
            category=category or "General",
            uploaded_by=admin_id,
        )

        doc_id = int(doc.id)

        # 4. Extract text
        try:
            if ext == ".pdf":
                extracted_pages = extract_text_from_pdf(file_path)
            elif ext == ".docx":
                extracted_pages = extract_text_from_docx(file_path)
            else:
                extracted_pages = extract_text_from_txt(file_path)
        except Exception as e:
            Repository.delete_document(db, doc_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to extract text from document: {str(e)}",
            )

        if not extracted_pages:
            Repository.delete_document(db, doc_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document contains no readable text.",
            )

        # 5. Chunk text
        chunks_data = chunk_extracted_pages(extracted_pages)
        if not chunks_data:
            Repository.delete_document(db, doc_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document produced no chunks after text cleaning.",
            )

        # 6. Save chunks to database
        db_chunks = Repository.create_chunks(db, doc_id, chunks_data)

        # 7. Embed & Store in Vector DB
        chunk_texts = [str(c.chunk_text) for c in db_chunks]
        embeddings = get_embeddings_batch(chunk_texts)

        vector_chunk_ids = [str(c.id) for c in db_chunks]
        vector_metadatas = [
            {
                "document_id": doc_id,
                "document_name": str(doc.file_name),
                "document_title": str(doc.title),
                "page": int(c.page_number or 1),
                "section": str(c.section or "General"),
            }
            for c in db_chunks
        ]

        vector_store.add_chunks(
            chunk_ids=vector_chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=vector_metadatas,
        )

        return doc

    @staticmethod
    def get_all_documents(db: Session):
        docs = Repository.get_all_documents(db)
        result = []
        for d in docs:
            chunk_count = len(d.chunks)
            upload_dt = (
                d.upload_date.strftime("%Y-%m-%d %H:%M")
                if hasattr(d.upload_date, "strftime")
                else str(d.upload_date)
            )
            result.append(
                {
                    "id": d.id,
                    "file_name": d.file_name,
                    "file_type": d.file_type,
                    "title": d.title,
                    "department": d.department,
                    "category": d.category,
                    "upload_date": upload_dt,
                    "status": d.status,
                    "chunks_count": chunk_count,
                }
            )
        return result

    @staticmethod
    def delete_document(db: Session, doc_id: int):
        doc = Repository.get_document_by_id(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        # Delete from vector store
        vector_store.delete_by_document(doc_id)

        # Delete from filesystem
        doc_path = str(doc.file_path)
        if os.path.exists(doc_path):
            try:
                os.remove(doc_path)
            except Exception as e:
                print(f"File delete error: {e}")

        # Cascading delete from DB
        Repository.delete_document(db, doc_id)
        return {
            "message": "Document and associated vector chunks deleted successfully."
        }

    @staticmethod
    def reprocess_document(db: Session, doc_id: int):
        doc = Repository.get_document_by_id(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        # 1. Clear old chunks from Vector Store & DB
        vector_store.delete_by_document(doc_id)
        Repository.delete_chunks_by_document(db, doc_id)

        # 2. Extract text again
        file_path_str = str(doc.file_path)
        ext = str(doc.file_type).lower()
        if ext == "pdf":
            pages = extract_text_from_pdf(file_path_str)
        elif ext == "docx":
            pages = extract_text_from_docx(file_path_str)
        else:
            pages = extract_text_from_txt(file_path_str)

        chunks_data = chunk_extracted_pages(pages)
        db_chunks = Repository.create_chunks(db, doc_id, chunks_data)

        # 3. Embed & Vector store update
        chunk_texts = [str(c.chunk_text) for c in db_chunks]
        embeddings = get_embeddings_batch(chunk_texts)
        vector_ids = [str(c.id) for c in db_chunks]
        vector_metas = [
            {
                "document_id": doc_id,
                "document_name": str(doc.file_name),
                "document_title": str(doc.title),
                "page": int(c.page_number or 1),
                "section": str(c.section or "General"),
            }
            for c in db_chunks
        ]
        vector_store.add_chunks(vector_ids, embeddings, chunk_texts, vector_metas)

        doc.version = int(doc.version) + 1  # type: ignore
        doc.status = "PROCESSED"  # type: ignore
        db.commit()

        return {"message": "Document reprocessed successfully.", "version": doc.version}
