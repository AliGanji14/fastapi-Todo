from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from users.schemas import UserLoginSchema, UserRegisterSchema, UserRefreshTokenSchema
from users.models import UserModel
from sqlalchemy.orm import Session
from core.database import get_db
import secrets
from auth.jwt_auth import (
    generate_access_token,
    generate_regresh_token,
    decode_refresh_token,
)

router = APIRouter(tags=["users"], prefix="/users")


def generate_token():
    return secrets.token_hex(32)


@router.post("/login")
async def user_login(request: UserLoginSchema, db: Session = Depends(get_db)):
    user_obj = db.query(UserModel).filter_by(
        username=request.username.lower()).first()
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid user for password"
        )
    if not user_obj.verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid user for password"
        )

    access_token = generate_access_token(user_obj.id)
    refresh_token = generate_regresh_token(user_obj.id)
    return JSONResponse(
        content={
            "detail": "logged in successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )


@router.post("/register")
async def user_register(request: UserRegisterSchema, db: Session = Depends(get_db)):
    if db.query(UserModel).filter_by(username=request.username.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="username already exists"
        )
    user_obj = UserModel(username=request.username.lower())
    user_obj.set_password(request.password)
    db.add(user_obj)
    db.commit()
    return JSONResponse(content={"detail": "user registered successfully"})


@router.post("/refresh-token")
async def user_refresh_token(
    request: UserRefreshTokenSchema, db: Session = Depends(get_db)
):
    user_id = decode_refresh_token(request.token)
    access_token = generate_access_token(user_id)
    return JSONResponse(content={"access_token": access_token})
