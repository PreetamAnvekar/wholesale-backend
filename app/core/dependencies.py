from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import  JWTError
from sqlalchemy.orm import Session
from jose import jwt

from app.db.session import get_db
from app.models.admin_users import AdminUser
from app.core.jwt import SECRET_KEY, ALGORITHM


security = HTTPBearer()

# def get_current_admin(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     db: Session = Depends(get_db)
# ):
#     token = credentials.credentials

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         admin_id: str = payload.get("sub")
#         if not admin_id:
#             raise HTTPException(status_code=401, detail="Invalid token")
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

#     admin = db.query(AdminUser).filter(
#         AdminUser.admin_id == admin_id,
#         AdminUser.is_active == True
#     ).first()

#     if not admin:
#         raise HTTPException(status_code=401, detail="Admin not found")

#     return admin

from fastapi import Request
from fastapi import Depends, HTTPException, Header
from app.core.security import decode_token
from jose import ExpiredSignatureError, JWTError

def get_current_admin(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("admin_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        payload = decode_token(token)
        admin_id = payload.get("sub")

        if not admin_id:
            raise HTTPException(401, "Invalid token payload")

    except ExpiredSignatureError:
        raise HTTPException(401, "Session expired")
    except JWTError:
        raise HTTPException(401, "Invalid session")

    admin = db.query(AdminUser).filter(
        AdminUser.admin_id == admin_id,
        AdminUser.is_active == True
    ).first()

    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Admin not found or inactive"
        )

    return admin


def admin_only(admin=Depends(get_current_admin)):
    if admin.role not in ["admin", "super_admin"]:
        raise HTTPException(403, "Admin access required")
    return admin

def super_admin_only(admin=Depends(get_current_admin)):
    if admin.role != "super_admin":
        raise HTTPException(403, "Super admin only")
    return admin



from fastapi import Request, Response
from app.core.config import settings
import uuid, hashlib, time

def generate_session_id():
    raw = f"{uuid.uuid4()}:{int(time.time())}"
    return hashlib.sha256(raw.encode()).hexdigest()

def get_user_session(
    request: Request,
    response: Response
):
    session_id = request.cookies.get("user_session")

    if not session_id:
        session_id = generate_session_id()
        response.set_cookie(
            key="user_session",
            value=session_id,
            max_age=86400,
            httponly=True,
            secure=settings.ENV == "production",
            samesite="lax",
            path="/"
        )
    return session_id

