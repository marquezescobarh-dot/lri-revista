from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Optional, List
from datetime import datetime
from database import get_db
import models, schemas, auth
import os, uuid, json
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/articulos", tags=["Artículos"])

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 10))
ALLOWED_DOC = {".pdf", ".docx"}
ALLOWED_EXTRA = {".pdf", ".docx", ".xlsx", ".xls", ".csv"}
ALLOWED_IMG = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def guardar_archivo_generico(archivo: UploadFile, carpeta: str, extensiones_ok: set) -> tuple:
    ext = os.path.splitext(archivo.filename)[1].lower()
    if ext not in extensiones_ok:
        raise HTTPException(status_code=400, detail=f"Formato no permitido: {ext}")
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"{uuid.uuid4()}{ext}"
    ruta = os.path.join(carpeta, nombre)
    contenido = archivo.file.read()
    if len(contenido) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Archivo muy grande (máx {MAX_FILE_SIZE_MB}MB)")
    with open(ruta, "wb") as f:
        f.write(contenido)
    tipo_map = {".pdf": "pdf", ".docx": "docx", ".xlsx": "xlsx", ".xls": "xlsx",
                ".csv": "csv", ".jpg": "imagen", ".jpeg": "imagen",
                ".png": "imagen", ".webp": "imagen", ".gif": "imagen"}
    return nombre, tipo_map.get(ext, "otro"), len(contenido) // 1024


@router.get("/", response_model=List[schemas.ArticuloLista])
def listar_articulos(zona: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Articulo).filter(models.Articulo.estado == "aprobado")
    if zona:
        q = q.filter(models.Articulo.zona == zona)
    return q.order_by(models.Articulo.creado_en.desc()).all()


@router.get("/top/semana")
def top_semana(db: Session = Depends(get_db)):
    from datetime import timedelta
    hace7 = datetime.utcnow() - timedelta(days=7)
    top = db.query(
        models.Articulo,
        func.count(models.Like.id).label("total_likes")
    ).outerjoin(models.Like, models.Like.articulo_id == models.Articulo.id
    ).filter(models.Articulo.estado == "aprobado"
    ).group_by(models.Articulo.id
    ).order_by(func.count(models.Like.id).desc()).limit(5).all()

    return [{"id": a.id, "titulo": a.titulo, "resumen": a.resumen,
             "zona": a.zona, "autor": a.autor.nombre,
             "likes": likes, "creado_en": a.creado_en} for a, likes in top]


@router.get("/mis/articulos", response_model=List[schemas.ArticuloLista])
def mis_articulos(usuario: models.Usuario = Depends(auth.requerir_login), db: Session = Depends(get_db)):
    return db.query(models.Articulo).filter(
        models.Articulo.autor_id == usuario.id,
        models.Articulo.estado != "eliminado"
    ).order_by(models.Articulo.creado_en.desc()).all()


@router.get("/{articulo_id}", response_model=schemas.ArticuloPublico)
def ver_articulo(articulo_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not a or a.estado == "eliminado":
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    if a.estado not in ("aprobado",):
        raise HTTPException(status_code=404, detail="Artículo no disponible")
    return a




@router.get("/{articulo_id}/ver-pdf")
def ver_pdf_publico(articulo_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not a or not a.archivo_url or a.tipo_archivo != "pdf":
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    ruta = os.path.join(UPLOAD_FOLDER, "articulos", a.archivo_url)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no disponible")
    return FileResponse(ruta, media_type="application/pdf", headers={"Content-Disposition": "inline"})

@router.get("/{articulo_id}/descargar")
def descargar_archivo(
    articulo_id: int,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    a = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not a or not a.archivo_url:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    ruta = os.path.join(UPLOAD_FOLDER, "articulos", a.archivo_url)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no disponible")
    return FileResponse(ruta, filename=a.archivo_url)


@router.get("/{articulo_id}/archivos/{archivo_id}/descargar")
def descargar_archivo_extra(
    articulo_id: int,
    archivo_id: int,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    archivo = db.query(models.ArchivoArticulo).filter(
        models.ArchivoArticulo.id == archivo_id,
        models.ArchivoArticulo.articulo_id == articulo_id
    ).first()
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    ruta = os.path.join(UPLOAD_FOLDER, "extras", archivo.nombre_guardado)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no disponible")
    return FileResponse(ruta, filename=archivo.nombre_original)


@router.post("/imagen-editor")
async def subir_imagen_editor(
    imagen: UploadFile = File(...),
    usuario: models.Usuario = Depends(auth.requerir_login)
):
    nombre, _, _ = guardar_archivo_generico(imagen, os.path.join(UPLOAD_FOLDER, "editor"), ALLOWED_IMG)
    return {"url": f"/uploads/editor/{nombre}"}


@router.post("/editor", response_model=schemas.ArticuloPublico, status_code=201)
async def publicar_con_editor(
    titulo: str = Form(...),
    zona: str = Form(...),
    resumen: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    seccion: Optional[str] = Form(None),
    contenido_html: str = Form(...),
    imagen_portada: Optional[UploadFile] = File(None),
    archivos_extra: Optional[List[UploadFile]] = File(None),
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    if len(contenido_html.strip()) < 20:
        raise HTTPException(status_code=400, detail="El contenido es muy corto")

    imagen_url = None
    if imagen_portada and imagen_portada.filename:
        ext = os.path.splitext(imagen_portada.filename)[1].lower()
        if ext in ALLOWED_IMG:
            os.makedirs(os.path.join(UPLOAD_FOLDER, "portadas"), exist_ok=True)
            nombre_img = f"{uuid.uuid4()}{ext}"
            with open(os.path.join(UPLOAD_FOLDER, "portadas", nombre_img), "wb") as f:
                f.write(await imagen_portada.read())
            imagen_url = nombre_img

    estado_inicial = "aprobado" if zona == "libre" else "pendiente"
    articulo = models.Articulo(
        autor_id=usuario.id,
        organizacion_id=usuario.organizacion_id,
        titulo=titulo, resumen=resumen,
        contenido_html=contenido_html,
        tipo_contenido="editor",
        imagen_portada=imagen_url,
        zona=zona, estado=estado_inicial,
        tags=tags, seccion=seccion
    )
    db.add(articulo)
    db.commit()
    db.refresh(articulo)

    if archivos_extra:
        for f in archivos_extra:
            if f and f.filename:
                try:
                    nombre, tipo, kb = guardar_archivo_generico(
                        f, os.path.join(UPLOAD_FOLDER, "extras"), ALLOWED_EXTRA
                    )
                    extra = models.ArchivoArticulo(
                        articulo_id=articulo.id,
                        nombre_original=f.filename,
                        nombre_guardado=nombre,
                        tipo=tipo, tamanio_kb=kb
                    )
                    db.add(extra)
                except: pass
        db.commit()
        db.refresh(articulo)

    return articulo


@router.post("/subir-archivo", response_model=schemas.ArticuloPublico, status_code=201)
async def publicar_con_archivo(
    titulo: str = Form(...),
    zona: str = Form(...),
    resumen: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    seccion: Optional[str] = Form(None),
    archivo: UploadFile = File(...),
    imagen_portada: Optional[UploadFile] = File(None),
    archivos_extra: Optional[List[UploadFile]] = File(None),
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    nombre_arch, tipo, kb = guardar_archivo_generico(
        archivo, os.path.join(UPLOAD_FOLDER, "articulos"), ALLOWED_DOC
    )

    imagen_url = None
    if imagen_portada and imagen_portada.filename:
        ext = os.path.splitext(imagen_portada.filename)[1].lower()
        if ext in ALLOWED_IMG:
            os.makedirs(os.path.join(UPLOAD_FOLDER, "portadas"), exist_ok=True)
            nombre_img = f"{uuid.uuid4()}{ext}"
            with open(os.path.join(UPLOAD_FOLDER, "portadas", nombre_img), "wb") as f:
                f.write(await imagen_portada.read())
            imagen_url = nombre_img

    estado_inicial = "aprobado" if zona == "libre" else "pendiente"
    articulo = models.Articulo(
        autor_id=usuario.id,
        organizacion_id=usuario.organizacion_id,
        titulo=titulo, resumen=resumen,
        archivo_url=nombre_arch, tipo_archivo=tipo,
        tipo_contenido="archivo",
        imagen_portada=imagen_url,
        zona=zona, estado=estado_inicial,
        tags=tags, seccion=seccion
    )
    db.add(articulo)
    db.commit()
    db.refresh(articulo)

    if archivos_extra:
        for f in archivos_extra:
            if f and f.filename:
                try:
                    nombre, tipo_extra, kb_e = guardar_archivo_generico(
                        f, os.path.join(UPLOAD_FOLDER, "extras"), ALLOWED_EXTRA
                    )
                    extra = models.ArchivoArticulo(
                        articulo_id=articulo.id,
                        nombre_original=f.filename,
                        nombre_guardado=nombre,
                        tipo=tipo_extra, tamanio_kb=kb_e
                    )
                    db.add(extra)
                except: pass
        db.commit()
        db.refresh(articulo)

    return articulo


@router.put("/{articulo_id}", response_model=schemas.ArticuloPublico)
async def editar_articulo(
    articulo_id: int,
    titulo: Optional[str] = Form(None),
    resumen: Optional[str] = Form(None),
    contenido_html: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    seccion: Optional[str] = Form(None),
    imagen_portada: Optional[UploadFile] = File(None),
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    articulo = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not articulo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    if articulo.autor_id != usuario.id and usuario.rol not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="No puedes editar este artículo")

    if titulo: articulo.titulo = titulo
    if resumen is not None: articulo.resumen = resumen
    if contenido_html: articulo.contenido_html = contenido_html
    if tags is not None: articulo.tags = tags
    if seccion is not None: articulo.seccion = seccion

    if imagen_portada and imagen_portada.filename:
        ext = os.path.splitext(imagen_portada.filename)[1].lower()
        if ext in ALLOWED_IMG:
            os.makedirs(os.path.join(UPLOAD_FOLDER, "portadas"), exist_ok=True)
            nombre_img = f"{uuid.uuid4()}{ext}"
            with open(os.path.join(UPLOAD_FOLDER, "portadas", nombre_img), "wb") as f:
                f.write(await imagen_portada.read())
            articulo.imagen_portada = nombre_img

    articulo.editado_en = datetime.utcnow()
    if articulo.zona == "academico" and articulo.estado == "aprobado":
        articulo.estado = "pendiente"

    db.commit()
    db.refresh(articulo)
    return articulo


@router.delete("/{articulo_id}", response_model=schemas.Mensaje)
def eliminar_mi_articulo(
    articulo_id: int,
    usuario: models.Usuario = Depends(auth.requerir_login),
    db: Session = Depends(get_db)
):
    articulo = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not articulo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    if articulo.autor_id != usuario.id and usuario.rol not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="No puedes eliminar este artículo")

    articulo.estado = "eliminado"
    db.commit()
    return {"mensaje": "Artículo eliminado"}


@router.post("/{articulo_id}/reportar", response_model=schemas.Mensaje)
def reportar_articulo(
    articulo_id: int,
    datos: schemas.ReporteCrear,
    db: Session = Depends(get_db)
):
    a = db.query(models.Articulo).filter(
        models.Articulo.id == articulo_id,
        models.Articulo.estado == "aprobado"
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    reporte = models.Reporte(
        articulo_id=articulo_id,
        nombre_reportador=datos.nombre_reportador,
        email_reportador=datos.email_reportador,
        razon=datos.razon,
        descripcion=datos.descripcion
    )
    db.add(reporte)
    db.commit()
    return {"mensaje": "Reporte enviado. Lo revisaremos pronto."}