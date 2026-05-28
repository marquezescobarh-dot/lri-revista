from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models, auth, os, uuid

router = APIRouter(prefix="/contacto", tags=["Contacto"])

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")


@router.post("/")
async def enviar_mensaje(
    nombre: str = Form(...),
    email: str = Form(...),
    asunto: str = Form(...),
    mensaje: str = Form(...),
    imagen: Optional[UploadFile] = File(None),
    usuario: Optional[models.Usuario] = Depends(auth.obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    imagen_url = None
    if imagen and imagen.filename:
        ext = os.path.splitext(imagen.filename)[1].lower()
        if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            os.makedirs(os.path.join(UPLOAD_FOLDER, "contacto"), exist_ok=True)
            nombre_img = f"{uuid.uuid4()}{ext}"
            ruta = os.path.join(UPLOAD_FOLDER, "contacto", nombre_img)
            contenido = await imagen.read()
            with open(ruta, "wb") as f:
                f.write(contenido)
            imagen_url = nombre_img

    msg = models.MensajeContacto(
        nombre=nombre,
        email=email,
        asunto=asunto,
        mensaje=mensaje,
        imagen_url=imagen_url,
        usuario_id=usuario.id if usuario else None
    )
    db.add(msg)
    db.commit()
    return {"mensaje": "Mensaje enviado. Te responderemos pronto."}


@router.get("/")
def ver_mensajes(
    admin: models.Usuario = Depends(auth.requerir_admin),
    db: Session = Depends(get_db)
):
    msgs = db.query(models.MensajeContacto).order_by(
        models.MensajeContacto.creado_en.desc()
    ).all()
    return [
        {
            "id": m.id,
            "nombre": m.nombre,
            "email": m.email,
            "asunto": m.asunto,
            "mensaje": m.mensaje,
            "imagen_url": m.imagen_url,
            "revisado": m.revisado,
            "creado_en": m.creado_en
        }
        for m in msgs
    ]


@router.post("/{msg_id}/revisar")
def marcar_revisado(
    msg_id: int,
    admin: models.Usuario = Depends(auth.requerir_admin),
    db: Session = Depends(get_db)
):
    m = db.query(models.MensajeContacto).filter(models.MensajeContacto.id == msg_id).first()
    if m:
        m.revisado = True
        db.commit()
    return {"mensaje": "Marcado como revisado"}
