from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models, auth
from routers.notificaciones_router import crear_notificacion

router = APIRouter(prefix="/articulos", tags=["Likes"])


@router.post("/{articulo_id}/like")
def dar_like(
    articulo_id: int,
    request: Request,
    usuario: Optional[models.Usuario] = Depends(auth.obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    a = db.query(models.Articulo).filter(models.Articulo.id == articulo_id, models.Articulo.estado == "aprobado").first()
    if not a:
        return {"error": "No encontrado"}

    ip = request.client.host
    q = db.query(models.Like).filter(models.Like.articulo_id == articulo_id)
    existe = q.filter(models.Like.usuario_id == usuario.id).first() if usuario else q.filter(models.Like.ip_address == ip).first()

    if existe:
        db.delete(existe)
        db.commit()
        total = db.query(models.Like).filter(models.Like.articulo_id == articulo_id).count()
        return {"likes": total, "liked": False}
    else:
        lk = models.Like(articulo_id=articulo_id, usuario_id=usuario.id if usuario else None, ip_address=ip if not usuario else None)
        db.add(lk)
        db.commit()
        total = db.query(models.Like).filter(models.Like.articulo_id == articulo_id).count()
        if usuario and a.autor_id != usuario.id:
            from ranking_service import dar_puntos
            dar_puntos(db, a.autor_id, models.PUNTOS_ACCIONES["like_recibido"], f"Like en '{a.titulo[:40]}'")
            if total % 10 == 0:
                crear_notificacion(db, a.autor_id, "like_recibido", f"Tu artículo '{a.titulo[:50]}' alcanzó {total} likes", f"/pages/articulo.html?id={articulo_id}")
        return {"likes": total, "liked": True}


@router.get("/{articulo_id}/likes")
def contar_likes(
    articulo_id: int,
    request: Request,
    usuario: Optional[models.Usuario] = Depends(auth.obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    total = db.query(models.Like).filter(models.Like.articulo_id == articulo_id).count()
    ip = request.client.host
    q = db.query(models.Like).filter(models.Like.articulo_id == articulo_id)
    liked = bool(q.filter(models.Like.usuario_id == usuario.id).first()) if usuario else bool(q.filter(models.Like.ip_address == ip).first())
    return {"likes": total, "liked": liked}
