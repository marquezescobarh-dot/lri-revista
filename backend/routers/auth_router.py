from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from email_service import generar_codigo, codigo_expiracion, enviar_email_verificacion
from datetime import datetime
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class RecuperarRequest(BaseModel):
    email: EmailStr

class ResetRequest(BaseModel):
    email: EmailStr
    codigo: str
    nueva_contrasena: str


@router.post("/registro", response_model=schemas.Token, status_code=201)
def registrarse(datos: schemas.UsuarioRegistro, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")

    codigo = generar_codigo()
    nuevo_usuario = models.Usuario(
        nombre=datos.nombre,
        email=datos.email,
        contrasena_hash=auth.hashear_password(datos.contrasena),
        rol="estudiante",
        email_verificado=False,
        codigo_verificacion=codigo,
        codigo_expira=codigo_expiracion(),
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    enviar_email_verificacion(datos.email, datos.nombre, codigo)
    token = auth.crear_token({"sub": nuevo_usuario.email})
    return {"access_token": token, "token_type": "bearer", "usuario": nuevo_usuario}


@router.post("/verificar-email", response_model=schemas.Mensaje)
def verificar_email(datos: schemas.VerificarEmail, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.email_verificado:
        return {"mensaje": "Email ya verificado"}
    if usuario.codigo_verificacion != datos.codigo:
        raise HTTPException(status_code=400, detail="Código incorrecto")
    if usuario.codigo_expira and datetime.utcnow() > usuario.codigo_expira:
        raise HTTPException(status_code=400, detail="El código expiró. Solicita uno nuevo.")
    usuario.email_verificado = True
    usuario.codigo_verificacion = None
    usuario.codigo_expira = None
    db.commit()
    return {"mensaje": "¡Email verificado! Ya puedes publicar."}


@router.post("/reenviar-codigo", response_model=schemas.Mensaje)
def reenviar_codigo(datos: RecuperarRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.email_verificado:
        return {"mensaje": "Email ya verificado"}
    codigo = generar_codigo()
    usuario.codigo_verificacion = codigo
    usuario.codigo_expira = codigo_expiracion()
    db.commit()
    enviar_email_verificacion(datos.email, usuario.nombre, codigo)
    return {"mensaje": "Código reenviado a tu correo"}


@router.post("/recuperar-contrasena", response_model=schemas.Mensaje)
def recuperar_contrasena(datos: RecuperarRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese email")
    codigo = generar_codigo()
    usuario.codigo_verificacion = codigo
    usuario.codigo_expira = codigo_expiracion()
    db.commit()
    enviar_recuperacion(datos.email, usuario.nombre, codigo)
    return {"mensaje": "Te enviamos un código a tu correo"}


@router.post("/reset-contrasena", response_model=schemas.Mensaje)
def reset_contrasena(datos: ResetRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.codigo_verificacion != datos.codigo:
        raise HTTPException(status_code=400, detail="Código incorrecto")
    if usuario.codigo_expira and datetime.utcnow() > usuario.codigo_expira:
        raise HTTPException(status_code=400, detail="El código expiró. Solicita uno nuevo.")
    if len(datos.nueva_contrasena) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
    usuario.contrasena_hash = auth.hashear_password(datos.nueva_contrasena)
    usuario.codigo_verificacion = None
    usuario.codigo_expira = None
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}


@router.post("/login", response_model=schemas.Token)
def iniciar_sesion(datos: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario or not auth.verificar_password(datos.contrasena, usuario.contrasena_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada")
    token = auth.crear_token({"sub": usuario.email}, recordarme=datos.recordarme)
    return {"access_token": token, "token_type": "bearer", "usuario": usuario}


@router.get("/yo", response_model=schemas.UsuarioConEmail)
def mi_perfil(usuario_actual: models.Usuario = Depends(auth.requerir_login)):
    return usuario_actual


def enviar_recuperacion(email: str, nombre: str, codigo: str):
    from email_service import SMTP_EMAIL, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"\n{'='*50}")
        print(f"[DEV] Código de recuperación para {email}: {codigo}")
        print(f"{'='*50}\n")
        return

    html = f"""
    <!DOCTYPE html><html><body style="font-family:'Georgia',serif;background:#FAFAF7;margin:0;padding:2rem">
    <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;border:1.5px solid #DDD9CF">
      <div style="background:#003580;padding:2rem;text-align:center">
        <h1 style="color:#C9963A;font-size:1.8rem;margin:0;letter-spacing:2px">LRI</h1>
        <p style="color:rgba(255,255,255,0.7);font-size:0.8rem;margin:0.3rem 0 0;font-family:Arial,sans-serif">La Riqueza de las Ideas · UNAM</p>
      </div>
      <div style="padding:2rem">
        <h2 style="color:#1A1A1A;margin-bottom:0.5rem">Recuperar contraseña</h2>
        <p style="color:#6B6560;font-size:0.95rem;line-height:1.7">Hola <strong>{nombre}</strong>, recibimos una solicitud para restablecer tu contraseña. Tu código es:</p>
        <div style="background:#E8EFF9;border:2px solid #003580;border-radius:12px;padding:1.5rem;text-align:center;margin:1.5rem 0">
          <span style="font-family:monospace;font-size:2.5rem;font-weight:700;color:#003580;letter-spacing:8px">{codigo}</span>
        </div>
        <p style="color:#9E9890;font-size:0.82rem;text-align:center">Expira en <strong>15 minutos</strong>. Si no solicitaste esto, ignora este mensaje.</p>
      </div>
      <div style="background:#003580;padding:1rem 2rem;text-align:center">
        <p style="color:rgba(255,255,255,0.5);font-size:0.75rem;margin:0">© 2026 La Riqueza de las Ideas · Facultad de Economía, UNAM</p>
      </div>
    </div></body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Recuperar contraseña LRI: {codigo}"
        msg["From"] = f"La Riqueza de las Ideas <{SMTP_EMAIL}>"
        msg["To"] = email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
    except Exception as e:
        print(f"[FALLBACK] Código recuperación para {email}: {codigo}")