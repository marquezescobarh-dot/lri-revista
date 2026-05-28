from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
import models, auth

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


def crear_notificacion(db: Session, usuario_id: int, tipo: str, mensaje: str, link: str = None):
    n = models.Notificacion(usuario_id=usuario_id, tipo=tipo, mensaje=mensaje, link=link)
    db.add(n)
    db.commit()


@router.get("/")
def mis_notificaciones(
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    notifs = db.query(models.Notificacion).filter(
        models.Notificacion.usuario_id == usuario.id
    ).order_by(desc(models.Notificacion.creado_en)).limit(30).all()
    return [
        {
            "id": n.id,
            "tipo": n.tipo,
            "mensaje": n.mensaje,
            "link": n.link,
            "leida": n.leida,
            "creado_en": n.creado_en
        }
        for n in notifs
    ]


@router.get("/no-leidas")
def contar_no_leidas(
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    count = db.query(models.Notificacion).filter(
        models.Notificacion.usuario_id == usuario.id,
        models.Notificacion.leida == False
    ).count()
    return {"count": count}


@router.post("/marcar-leidas")
def marcar_todas_leidas(
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    db.query(models.Notificacion).filter(
        models.Notificacion.usuario_id == usuario.id,
        models.Notificacion.leida == False
    ).update({"leida": True})
    db.commit()
    return {"mensaje": "Notificaciones marcadas como leídas"}


@router.post("/{notif_id}/leer")
def marcar_leida(
    notif_id: int,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    n = db.query(models.Notificacion).filter(
        models.Notificacion.id == notif_id,
        models.Notificacion.usuario_id == usuario.id
    ).first()
    if n:
        n.leida = True
        db.commit()
    return {"mensaje": "OK"}
