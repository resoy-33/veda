"""Authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import (
    JWT_EXPIRES_SECONDS,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import connect

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    hedera_account_id: str
    display_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ProfileUpdate(BaseModel):
    display_name: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    email = body.email.strip().lower()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, role, hedera_account_id, display_name "
            "FROM users WHERE email = %s",
            (email,),
        ).fetchone()
    if row is None or not verify_password(body.password, row[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    user = {
        "id": str(row[0]),
        "email": row[1],
        "role": row[3],
        "hedera_account_id": row[4],
        "display_name": row[5],
    }
    return TokenResponse(
        access_token=create_access_token(user),
        expires_in=JWT_EXPIRES_SECONDS,
        user=UserOut(**user),
    )


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)) -> UserOut:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, email, role, hedera_account_id, display_name "
            "FROM users WHERE id = %s",
            (user["id"],),
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )
    return UserOut(
        id=str(row[0]),
        email=row[1],
        role=row[2],
        hedera_account_id=row[3],
        display_name=row[4],
    )


@router.patch("/me", response_model=UserOut)
def update_me(
    body: ProfileUpdate,
    user: dict = Depends(get_current_user),
) -> UserOut:
    display_name = body.display_name.strip()
    if not display_name or len(display_name) > 80:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="display_name must be between 1 and 80 characters",
        )
    with connect() as conn:
        row = conn.execute(
            "UPDATE users SET display_name = %s WHERE id = %s "
            "RETURNING id, email, role, hedera_account_id, display_name",
            (display_name, user["id"]),
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )
    return UserOut(
        id=str(row[0]),
        email=row[1],
        role=row[2],
        hedera_account_id=row[3],
        display_name=row[4],
    )


@router.post("/change-password")
def change_password(
    body: PasswordChange,
    user: dict = Depends(get_current_user),
) -> dict:
    if len(body.new_password) < 8 or len(body.new_password) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit contenir au moins 8 caractères",
        )
    with connect() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = %s",
            (user["id"],),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )
        if not verify_password(body.current_password, row[0]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le mot de passe actuel est incorrect",
            )
        conn.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(body.new_password), user["id"]),
        )
    return {"status": "ok"}
