from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from database import get_db
import models, auth, ranking_service
from pydantic import BaseModel
import os, uuid

router = APIRouter(prefix="/perfil", tags=["Perfiles"])

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")


class PerfilUpdate(BaseModel):
    bio: Optional[str] = None
    tipo_usuario: Optional[str] = None
    universidad: Optional[str] = None
    facultad: Optional[str] = None
    carrera: Optional[str] = None
    semestre: Optional[int] = None
    pais: Optional[str] = None
    ciudad: Optional[str] = None
    areas_interes: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    email_publico: Optional[str] = None
    sitio_web: Optional[str] = None


def perfil_publico(u: models.Usuario, db: Session) -> dict:
    total_likes = db.query(func.count(models.Like.id)).join(
        models.Articulo, models.Like.articulo_id == models.Articulo.id
    ).filter(models.Articulo.autor_id == u.id).scalar() or 0

    total_articulos = db.query(models.Articulo).filter(
        models.Articulo.autor_id == u.id,
        models.Articulo.estado == "aprobado"
    ).count()

    total_comentarios = db.query(models.Comentario).filter(
        models.Comentario.usuario_id == u.id,
        models.Comentario.visible == True
    ).count()

    top_articulos = db.query(models.Articulo).filter(
        models.Articulo.autor_id == u.id,
        models.Articulo.estado == "aprobado"
    ).order_by(desc(models.Articulo.creado_en)).limit(3).all()

    nivel_info = ranking_service.get_nivel_info(u.puntos or 0)
    nivel_data = models.NIVELES[min((u.nivel or 1) - 1, len(models.NIVELES) - 1)]

    return {
        "id": u.id,
        "nombre": u.nombre,
        "foto_perfil": u.foto_perfil,
        "bio": u.bio,
        "tipo_usuario": u.tipo_usuario,
        "universidad": u.universidad,
        "facultad": u.facultad,
        "carrera": u.carrera,
        "semestre": u.semestre,
        "pais": u.pais,
        "ciudad": u.ciudad,
        "areas_interes": u.areas_interes,
        "twitter": u.twitter,
        "linkedin": u.linkedin,
        "email_publico": u.email_publico,
        "sitio_web": u.sitio_web,
        "puntos": u.puntos or 0,
        "nivel": u.nivel or 1,
        "nivel_titulo": nivel_data["titulo"],
        "nivel_emoji": nivel_data["emoji"],
        "nivel_info": nivel_info,
        "organizacion": {"id": u.organizacion.id, "nombre": u.organizacion.nombre} if u.organizacion else None,
        "rol": u.rol,
        "creado_en": u.creado_en.isoformat() if u.creado_en else None,
        "stats": {
            "articulos": total_articulos,
            "likes_recibidos": total_likes,
            "comentarios": total_comentarios
        },
        "top_articulos": [
            {"id": a.id, "titulo": a.titulo, "zona": a.zona, "creado_en": a.creado_en.isoformat()}
            for a in top_articulos
        ]
    }


@router.get("/ranking")
def top_ranking(db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).filter(
        models.Usuario.activo == True,
        models.Usuario.puntos > 0
    ).order_by(desc(models.Usuario.puntos)).limit(10).all()

    return [
        {
            "posicion": i + 1,
            "id": u.id,
            "nombre": u.nombre,
            "foto_perfil": u.foto_perfil,
            "puntos": u.puntos or 0,
            "nivel": u.nivel or 1,
            "nivel_titulo": models.NIVELES[min((u.nivel or 1) - 1, len(models.NIVELES) - 1)]["titulo"],
            "universidad": u.universidad,
            "carrera": u.carrera
        }
        for i, u in enumerate(usuarios)
    ]


@router.get("/niveles")
def info_niveles():
    return {"niveles": models.NIVELES, "puntos_acciones": models.PUNTOS_ACCIONES}


@router.get("/{usuario_id}")
def ver_perfil(usuario_id: int, db: Session = Depends(get_db)):
    u = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id,
        models.Usuario.activo == True
    ).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return perfil_publico(u, db)


@router.get("/yo/completo")
def mi_perfil_completo(
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    data = perfil_publico(usuario, db)
    data["email"] = usuario.email
    data["email_verificado"] = usuario.email_verificado
    historial = db.query(models.PuntosHistorial).filter(
        models.PuntosHistorial.usuario_id == usuario.id
    ).order_by(desc(models.PuntosHistorial.creado_en)).limit(20).all()
    data["historial_puntos"] = [
        {"puntos": h.puntos, "razon": h.razon, "fecha": h.creado_en.isoformat()}
        for h in historial
    ]
    return data


@router.put("/editar")
async def editar_perfil(
    bio: Optional[str] = Form(None),
    tipo_usuario: Optional[str] = Form(None),
    universidad: Optional[str] = Form(None),
    facultad: Optional[str] = Form(None),
    carrera: Optional[str] = Form(None),
    semestre: Optional[str] = Form(None),
    pais: Optional[str] = Form(None),
    ciudad: Optional[str] = Form(None),
    areas_interes: Optional[str] = Form(None),
    twitter: Optional[str] = Form(None),
    linkedin: Optional[str] = Form(None),
    email_publico: Optional[str] = Form(None),
    sitio_web: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    if bio is not None: usuario.bio = bio[:500] if bio else None
    if tipo_usuario: usuario.tipo_usuario = tipo_usuario
    if universidad is not None: usuario.universidad = universidad or None
    if facultad is not None: usuario.facultad = facultad or None
    if carrera is not None: usuario.carrera = carrera or None
    if semestre: usuario.semestre = int(semestre) if semestre.isdigit() else None
    if pais is not None: usuario.pais = pais or None
    if ciudad is not None: usuario.ciudad = ciudad or None
    if areas_interes is not None: usuario.areas_interes = areas_interes or None
    if twitter is not None: usuario.twitter = twitter.lstrip('@') or None
    if linkedin is not None: usuario.linkedin = linkedin or None
    if email_publico is not None: usuario.email_publico = email_publico or None
    if sitio_web is not None: usuario.sitio_web = sitio_web or None

    if foto and foto.filename:
        ext = os.path.splitext(foto.filename)[1].lower()
        if ext in {".jpg", ".jpeg", ".png", ".webp"}:
            os.makedirs(os.path.join(UPLOAD_FOLDER, "avatars"), exist_ok=True)
            nombre = f"{uuid.uuid4()}{ext}"
            ruta = os.path.join(UPLOAD_FOLDER, "avatars", nombre)
            contenido = await foto.read()
            with open(ruta, "wb") as f:
                f.write(contenido)
            usuario.foto_perfil = nombre

    db.commit()
    db.refresh(usuario)
    return perfil_publico(usuario, db)


@router.post("/admin/ajustar-puntos")
def ajustar_puntos(
    usuario_id: int,
    puntos: int,
    razon: str,
    admin: models.Usuario = Depends(auth.requerir_admin),
    db: Session = Depends(get_db)
):
    u = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    ranking_service.dar_puntos(db, usuario_id, puntos, f"Admin: {razon}")
    return {"mensaje": f"{'Dados' if puntos > 0 else 'Quitados'} {abs(puntos)} puntos a {u.nombre}"}