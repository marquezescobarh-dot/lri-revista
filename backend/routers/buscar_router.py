from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from database import get_db
from typing import Optional, List
import models, schemas

router = APIRouter(prefix="/buscar", tags=["Búsqueda"])

SECCIONES = [
    "Macroeconomía", "Microeconomía", "Finanzas", "Econometría",
    "Política económica", "Economía internacional", "Historia económica",
    "Economía laboral", "Desarrollo económico", "Economía ambiental",
    "Teoría económica", "Economía mexicana", "Otro"
]


@router.get("/articulos", response_model=List[schemas.ArticuloLista])
def buscar_articulos(
    q: Optional[str] = Query(None, description="Texto a buscar"),
    zona: Optional[str] = Query(None),
    seccion: Optional[str] = Query(None),
    autor: Optional[str] = Query(None),
    orden: Optional[str] = Query("reciente", description="reciente | likes | alfabetico"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Articulo).filter(models.Articulo.estado == "aprobado")

    if q:
        query = query.filter(
            or_(
                func.lower(models.Articulo.titulo).contains(q.lower()),
                func.lower(models.Articulo.resumen).contains(q.lower()),
                func.lower(models.Articulo.tags).contains(q.lower()),
            )
        )

    if zona and zona in ("academico", "libre"):
        query = query.filter(models.Articulo.zona == zona)

    if seccion:
        query = query.filter(
            func.lower(models.Articulo.tags).contains(seccion.lower())
        )

    if autor:
        query = query.join(models.Usuario, models.Articulo.autor_id == models.Usuario.id).filter(
            func.lower(models.Usuario.nombre).contains(autor.lower())
        )

    if orden == "likes":
        query = query.outerjoin(
            models.Like, models.Like.articulo_id == models.Articulo.id
        ).group_by(models.Articulo.id).order_by(func.count(models.Like.id).desc())
    elif orden == "alfabetico":
        query = query.order_by(func.lower(models.Articulo.titulo))
    else:
        query = query.order_by(models.Articulo.creado_en.desc())

    return query.limit(50).all()


@router.get("/secciones")
def obtener_secciones():
    return {"secciones": SECCIONES}