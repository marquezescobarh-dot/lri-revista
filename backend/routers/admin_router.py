from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth, ranking_service
from routers.notificaciones_router import crear_notificacion

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/resumen")
def resumen_admin(admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    return {
        "articulos_pendientes": db.query(models.Articulo).filter(models.Articulo.estado == "pendiente").count(),
        "reportes_sin_revisar": db.query(models.Reporte).filter(models.Reporte.revisado == False).count(),
        "articulos_publicados": db.query(models.Articulo).filter(models.Articulo.estado == "aprobado").count(),
        "usuarios_activos": db.query(models.Usuario).filter(models.Usuario.activo == True).count(),
        "total_likes": db.query(models.Like).count(),
        "mensajes_nuevos": db.query(models.MensajeContacto).filter(models.MensajeContacto.revisado == False).count(),
    }


@router.get("/articulos/pendientes")
def articulos_pendientes(admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    arts = db.query(models.Articulo).filter(models.Articulo.estado == "pendiente").order_by(models.Articulo.creado_en.asc()).all()
    return [{
            "id": a.id, "titulo": a.titulo, "resumen": a.resumen,
            "contenido_html": a.contenido_html, "zona": a.zona,
            "tipo_contenido": a.tipo_contenido, "tipo_archivo": a.tipo_archivo,
            "archivo_url": a.archivo_url, "tags": a.tags,
            "seccion": a.seccion, "estado": a.estado, "creado_en": a.creado_en,
            "autor": {
                "id": a.autor.id, "nombre": a.autor.nombre,
                "email": a.autor.email, "carrera": a.autor.carrera,
                "universidad": a.autor.universidad,
                "foto_perfil": a.autor.foto_perfil, "nivel": a.autor.nivel,
                "rol": a.autor.rol, "creado_en": a.autor.creado_en,
                "organizacion": None
            },
            "organizacion": None
        } for a in arts]


@router.get("/articulos/todos")
def todos_articulos(admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    arts = db.query(models.Articulo).filter(models.Articulo.estado != "eliminado").order_by(models.Articulo.creado_en.desc()).all()
    return [{
            "id": a.id, "titulo": a.titulo, "resumen": a.resumen,
            "contenido_html": a.contenido_html, "zona": a.zona,
            "tipo_contenido": a.tipo_contenido, "tipo_archivo": a.tipo_archivo,
            "archivo_url": a.archivo_url, "tags": a.tags,
            "seccion": a.seccion, "estado": a.estado, "creado_en": a.creado_en,
            "autor": {
                "id": a.autor.id, "nombre": a.autor.nombre,
                "email": a.autor.email, "carrera": a.autor.carrera,
                "universidad": a.autor.universidad,
                "foto_perfil": a.autor.foto_perfil, "nivel": a.autor.nivel,
                "rol": a.autor.rol, "creado_en": a.autor.creado_en,
                "organizacion": None
            },
            "organizacion": None
        } for a in arts]


@router.post("/articulos/{articulo_id}/aprobar")
def aprobar_articulo(articulo_id: int, datos: schemas.AccionAdminCrear, admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    a = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="No encontrado")
    a.estado = "aprobado"
    db.add(models.AccionAdmin(admin_id=admin.id, articulo_id=articulo_id, tipo_accion="aprobar", nota=datos.nota))
    pts = models.PUNTOS_ACCIONES["articulo_academico_aprobado"] if a.zona == "academico" else models.PUNTOS_ACCIONES["articulo_libre"]
    ranking_service.dar_puntos(db, a.autor_id, pts, f"Artículo aprobado: {a.titulo[:50]}")
    crear_notificacion(db, a.autor_id, "articulo_aprobado", f"Tu artículo '{a.titulo[:60]}' fue aprobado y publicado", f"/pages/articulo.html?id={articulo_id}")
    db.commit()
    return {"mensaje": "Artículo aprobado"}


@router.post("/articulos/{articulo_id}/rechazar")
def rechazar_articulo(articulo_id: int, datos: schemas.AccionAdminCrear, admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    a = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="No encontrado")
    a.estado = "rechazado"
    db.add(models.AccionAdmin(admin_id=admin.id, articulo_id=articulo_id, tipo_accion="rechazar", nota=datos.nota))
    crear_notificacion(db, a.autor_id, "articulo_rechazado", f"Tu artículo '{a.titulo[:60]}' necesita revisión antes de publicarse", f"/pages/perfil.html")
    db.commit()
    return {"mensaje": "Artículo rechazado"}


@router.post("/articulos/{articulo_id}/eliminar")
def eliminar_articulo(articulo_id: int, datos: schemas.AccionAdminCrear, admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    a = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="No encontrado")
    a.estado = "eliminado"
    db.add(models.AccionAdmin(admin_id=admin.id, articulo_id=articulo_id, tipo_accion="eliminar", nota=datos.nota))
    db.commit()
    return {"mensaje": "Artículo eliminado"}


@router.post("/comentarios/{comentario_id}/ocultar")
def ocultar_comentario(comentario_id: int, admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    c = db.query(models.Comentario).filter(models.Comentario.id == comentario_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="No encontrado")
    c.visible = False
    db.commit()
    return {"mensaje": "Comentario ocultado"}


@router.get("/reportes")
def ver_reportes(solo_sin_revisar: bool = True, admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    q = db.query(models.Reporte)
    if solo_sin_revisar:
        q = q.filter(models.Reporte.revisado == False)
    return q.order_by(models.Reporte.creado_en.desc()).all()


@router.post("/reportes/{reporte_id}/revisar")
def revisar_reporte(reporte_id: int, admin: models.Usuario = Depends(auth.requerir_admin), db: Session = Depends(get_db)):
    r = db.query(models.Reporte).filter(models.Reporte.id == reporte_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="No encontrado")
    r.revisado = True
    db.commit()
    return {"mensaje": "Marcado como revisado"}


@router.get("/usuarios")
def listar_usuarios(superadmin: models.Usuario = Depends(auth.requerir_superadmin), db: Session = Depends(get_db)):
    return [
        {
            "id": u.id, "nombre": u.nombre, "email": u.email,
            "carrera": u.carrera, "universidad": u.universidad,
            "rol": u.rol, "puntos": u.puntos or 0,
            "nivel": u.nivel or 1,
            "nivel_titulo": models.NIVELES[min((u.nivel or 1) - 1, len(models.NIVELES) - 1)]["titulo"],
            "activo": u.activo, "creado_en": u.creado_en
        }
        for u in db.query(models.Usuario).order_by(models.Usuario.creado_en.desc()).all()
    ]


@router.post("/usuarios/cambiar-rol")
def cambiar_rol(datos: schemas.CambiarRol, superadmin: models.Usuario = Depends(auth.requerir_superadmin), db: Session = Depends(get_db)):
    u = db.query(models.Usuario).filter(models.Usuario.id == datos.usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="No encontrado")
    if u.rol == "superadmin":
        raise HTTPException(status_code=403, detail="No puedes modificar al superadmin")
    u.rol = datos.nuevo_rol
    db.add(models.AccionAdmin(admin_id=superadmin.id, usuario_afectado_id=u.id, tipo_accion="asignar_admin" if datos.nuevo_rol == "admin" else "quitar_admin"))
    crear_notificacion(db, u.id, "rol_cambiado", f"Tu rol fue actualizado a {datos.nuevo_rol}", "/pages/perfil.html")
    db.commit()
    return {"mensaje": f"Rol de {u.nombre} actualizado a {datos.nuevo_rol}"}


@router.post("/usuarios/{usuario_id}/banear")
def banear_usuario(usuario_id: int, superadmin: models.Usuario = Depends(auth.requerir_superadmin), db: Session = Depends(get_db)):
    u = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="No encontrado")
    if u.rol == "superadmin":
        raise HTTPException(status_code=403, detail="No puedes banear al superadmin")
    u.activo = False
    db.commit()
    return {"mensaje": f"Usuario {u.nombre} baneado"}


@router.post("/usuarios/{usuario_id}/ajustar-puntos")
def ajustar_puntos(usuario_id: int, puntos: int, razon: str, superadmin: models.Usuario = Depends(auth.requerir_superadmin), db: Session = Depends(get_db)):
    u = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="No encontrado")
    ranking_service.dar_puntos(db, usuario_id, puntos, f"Admin: {razon}")
    crear_notificacion(db, usuario_id, "puntos_ajustados", f"Un admin {'agregó' if puntos > 0 else 'quitó'} {abs(puntos)} puntos a tu cuenta", "/pages/perfil.html")
    return {"mensaje": f"Puntos ajustados para {u.nombre}"}


@router.get("/log")
def ver_log(superadmin: models.Usuario = Depends(auth.requerir_superadmin), db: Session = Depends(get_db)):
    acciones = db.query(models.AccionAdmin).order_by(models.AccionAdmin.creado_en.desc()).limit(100).all()
    return [{"id": a.id, "admin": a.admin.nombre, "tipo_accion": a.tipo_accion, "articulo_id": a.articulo_id, "nota": a.nota, "fecha": a.creado_en} for a in acciones]
