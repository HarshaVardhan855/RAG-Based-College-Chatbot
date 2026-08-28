from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from database.repository import Repository
from auth.authentication import hash_password, verify_password, create_access_token
from config import settings
from database.models import UserRole


class UserService:
    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        full_name: str,
        role: str = UserRole.STUDENT.value,
        allow_admin: bool = False,
    ):
        """
        Registers a new user.
        SECURITY: 'allow_admin' is False by default — public self-registration is
        always forced to STUDENT role regardless of what the caller submits.
        Only internal calls (e.g., seed_admin_if_needed) may pass allow_admin=True.
        """
        existing_user = Repository.get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Enforce STUDENT role for all public self-registrations
        safe_role = role if allow_admin else UserRole.STUDENT.value

        hashed_pwd = hash_password(password)
        user = Repository.create_user(
            db=db,
            email=email,
            hashed_password=hashed_pwd,
            full_name=full_name,
            role=safe_role,
        )
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = Repository.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        user_hashed_pwd = str(user.hashed_password)
        if not verify_password(password, user_hashed_pwd):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        token = create_access_token(
            {"sub": str(user.id), "email": user.email, "role": user.role}
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            },
        }

    @staticmethod
    def seed_admin_if_needed(db: Session):
        admin = Repository.get_user_by_email(db, settings.ADMIN_EMAIL)
        if not admin:
            UserService.register_user(
                db=db,
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                full_name="College Administrator",
                role=UserRole.ADMIN.value,
                allow_admin=True,  # Internal call — allowed to create admin
            )
            print(f"Default admin created: {settings.ADMIN_EMAIL}")
