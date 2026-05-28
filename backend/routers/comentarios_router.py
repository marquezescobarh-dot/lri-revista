from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
import models, schemas, auth, ranking_service
from routers.notificaciones_router import crear_notificacion
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/articulos", tags=["Comentarios"])


class ComentarioCrearV2(BaseModel):
    contenido: str
    parent_id: Optional[int] = None


def serializar_comentario(c: models.Comentario, db: Session, usuario_actual=None) -> dict:
    nivel_idx = min((c.usuario.nivel or 1) - 1, len(models.NIVELES) - 1)
    nivel_data = models.NIVELES[nivel_idx]
    total_likes = len(c.likes)
    yo_di_like = False
    if usuario_actual:
        yo_di_like = any(lk.usuario_id == usuario_actual.id for lk in c.likes)

    respuestas = []
    for r in sorted(c.respuestas, key=lambda x: x.creado_en):
        if r.visible:
            respuestas.append(serializar_comentario(r, db, usuario_actual))

    return {
        "id": c.id,
        "contenido": c.contenido,
        "parent_id": c.parent_id,
        "creado_en": c.creado_en,
        "likes": total_likes,
        "yo_di_like": yo_di_like,
        "respuestas": respuestas,
        "usuario": {
            "id": c.usuario.id,
            "nombre": c.usuario.nombre,
            "foto_perfil": c.usuario.foto_perfil,
            "nivel_titulo": nivel_data["emoji"] + " " + nivel_data["titulo"],
            "organizacion": {"nombre": c.usuario.organizacion.nombre} if c.usuario.organizacion else None
        }
    }


@router.get("/{articulo_id}/comentarios")
def ver_comentarios(
    articulo_id: int,
    db: Session = Depends(get_db),
    usuario: Optional[models.Usuario] = Depends(auth.obtener_usuario_actual)
):
    a = db.query(models.Articulo).filter(
        models.Articulo.id == articulo_id,
        models.Articulo.estado == "aprobado"
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    comentarios_raiz = db.query(models.Comentario).filter(
        models.Comentario.articulo_id == articulo_id,
        models.Comentario.parent_id == None,
        models.Comentario.visible == True
    ).order_by(models.Comentario.creado_en.asc()).all()

    return [serializar_comentario(c, db, usuario) for c in comentarios_raiz]


@router.post("/{articulo_id}/comentarios")
def comentar(
    articulo_id: int,
    datos: ComentarioCrearV2,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    if not datos.contenido.strip() or len(datos.contenido) < 2:
        raise HTTPException(status_code=400, detail="El comentario está vacío")
    if len(datos.contenido) > 1000:
        raise HTTPException(status_code=400, detail="Máximo 1000 caracteres")

    a = db.query(models.Articulo).filter(
        models.Articulo.id == articulo_id,
        models.Articulo.estado == "aprobado"
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    c = models.Comentario(
        articulo_id=articulo_id,
        usuario_id=usuario.id,
        contenido=datos.contenido.strip(),
        parent_id=datos.parent_id
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    ranking_service.dar_puntos(db, usuario.id, models.PUNTOS_ACCIONES["comentario"], "Comentario publicado")

    if datos.parent_id:
        comentario_padre = db.query(models.Comentario).filter(models.Comentario.id == datos.parent_id).first()
        if comentario_padre and comentario_padre.usuario_id != usuario.id:
            crear_notificacion(
                db,
                comentario_padre.usuario_id,
                "respuesta_comentario",
                f"{usuario.nombre} respondió a tu comentario en '{a.titulo[:50]}'",
                f"/pages/articulo.html?id={articulo_id}"
            )
    else:
        if a.autor_id != usuario.id:
            crear_notificacion(
                db,
                a.autor_id,
                "comentario_nuevo",
                f"{usuario.nombre} comentó en tu artículo '{a.titulo[:50]}'",
                f"/pages/articulo.html?id={articulo_id}"
            )

    return {"mensaje": "Comentario publicado", "id": c.id}


@router.post("/{articulo_id}/comentarios/{comentario_id}/like")
def like_comentario(
    articulo_id: int,
    comentario_id: int,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    c = db.query(models.Comentario).filter(
        models.Comentario.id == comentario_id,
        models.Comentario.articulo_id == articulo_id,
        models.Comentario.visible == True
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")

    existe = db.query(models.LikeComentario).filter(
        models.LikeComentario.comentario_id == comentario_id,
        models.LikeComentario.usuario_id == usuario.id
    ).first()

    if existe:
        db.delete(existe)
        db.commit()
        total = db.query(models.LikeComentario).filter(models.LikeComentario.comentario_id == comentario_id).count()
        return {"likes": total, "liked": False}
    else:
        lk = models.LikeComentario(comentario_id=comentario_id, usuario_id=usuario.id)
        db.add(lk)
        db.commit()
        total = db.query(models.LikeComentario).filter(models.LikeComentario.comentario_id == comentario_id).count()
        return {"likes": total, "liked": True}


@router.delete("/{articulo_id}/comentarios/{comentario_id}")
def borrar_comentario(
    articulo_id: int,
    comentario_id: int,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    c = db.query(models.Comentario).filter(
        models.Comentario.id == comentario_id,
        models.Comentario.articulo_id == articulo_id,
        models.Comentario.usuario_id == usuario.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    c.visible = False
    db.commit()
    return {"mensaje": "Comentario eliminado"}
