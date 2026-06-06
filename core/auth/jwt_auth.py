from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from users.models import UserModel
from core.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import DecodeError, InvalidSignatureError
from core.config import settings

security = HTTPBearer()


def get_authenticate_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    token = credentials.credentials
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = decoded.get("user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication failed, user_id not found in the payload",
            )
        if decoded.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication failed, token type not valid",
            )
        if datetime.now() > datetime.fromtimestamp(decoded.get("exp")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication failed, token expired",
            )

        user_obj = db.query(UserModel).filter_by(id=user_id).one()
        return user_obj

    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication failed, invalid signature",
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication failed, decode failed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"authentication failed, {e}",
        )


def generate_access_token(user_id: int, expires_in: int = 3600):
    now = datetime.utcnow()
    payload = {
        "type": "access",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def generate_regresh_token(user_id: int, expires_in: int = 3600 * 24):
    now = datetime.utcnow()
    payload = {
        "type": "refresh",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_refresh_token(token):
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = decoded.get("user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication failed, user_id not found in the payload",
            )
        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication failed, token type not valid",
            )
        if datetime.now() > datetime.fromtimestamp(decoded.get("exp")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication failed, token expired",
            )

        return user_id

    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication failed, invalid signature",
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication failed, decode failed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"authentication failed, {e}",
        )
