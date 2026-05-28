from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models, os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REMEMBER_ME_EXPIRE_DAYS = int(os.getenv("REMEMBER_ME_EXPIRE_DAYS", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def verificar_password(password_plano: str, password_hash: str) -> bool:
    return pwd_context.verify(password_plano, password_hash)

def hashear_password(password: str) -> str:
    return pwd_context.hash(password)

def crear_token(data: dict, recordarme: bool = False) -> str:
    payload = data.copy()
    expira = datetime.utcnow() + (timedelta(days=REMEMBER_ME_EXPIRE_DAYS) if recordarme else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expira})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def obtener_usuario_actual(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[models.Usuario]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def requerir_login(usuario: Optional[models.Usuario] = Depends(obtener_usuario_actual)):
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Necesitas iniciar sesión")
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada")
    return usuario

def requerir_admin(usuario: models.Usuario = Depends(requerir_login)):
    if usuario.rol not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return usuario

def requerir_superadmin(usuario: models.Usuario = Depends(requerir_login)):
    if usuario.rol != "superadmin":
        raise HTTPException(status_code=403, detail="Solo el superadmin puede hacer esto")
    return usuario