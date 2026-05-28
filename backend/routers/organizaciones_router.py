from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/organizaciones", tags=["Organizaciones"])


@router.get("/", response_model=List[schemas.OrganizacionPublica])
def listar_organizaciones(
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Organizacion).filter(models.Organizacion.activa == True)
    if q:
        query = query.filter(
            func.lower(models.Organizacion.nombre).contains(q.lower())
        )
    return query.order_by(models.Organizacion.nombre).all()


@router.get("/{org_id}", response_model=schemas.OrganizacionPublica)
def ver_organizacion(org_id: int, db: Session = Depends(get_db)):
    org = db.query(models.Organizacion).filter(models.Organizacion.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return org


@router.post("/", response_model=schemas.OrganizacionPublica, status_code=201)
def crear_organizacion(
    datos: schemas.OrganizacionCrear,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    existe = db.query(models.Organizacion).filter(
        func.lower(models.Organizacion.nombre) == datos.nombre.lower()
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe una organización con ese nombre")

    org = models.Organizacion(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        tipo=datos.tipo
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    usuario.organizacion_id = org.id
    db.commit()

    return org


@router.post("/{org_id}/unirse", response_model=schemas.Mensaje)
def unirse_organizacion(
    org_id: int,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    org = db.query(models.Organizacion).filter(
        models.Organizacion.id == org_id,
        models.Organizacion.activa == True
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")

    usuario.organizacion_id = org_id
    db.commit()
    return {"mensaje": f"Te uniste a {org.nombre}"}


@router.post("/salir", response_model=schemas.Mensaje)
def salir_organizacion(
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    usuario.organizacion_id = None
    db.commit()
    return {"mensaje": "Saliste de la organización"}