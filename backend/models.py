from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

NIVELES = [
    {"nivel": 1, "titulo": "Lector",              "emoji": "📖", "puntos_min": 0},
    {"nivel": 2, "titulo": "Colaborador",          "emoji": "✍️", "puntos_min": 100},
    {"nivel": 3, "titulo": "Autor",                "emoji": "📝", "puntos_min": 300},
    {"nivel": 4, "titulo": "Autor Destacado",      "emoji": "⭐", "puntos_min": 700},
    {"nivel": 5, "titulo": "Investigador",          "emoji": "🎓", "puntos_min": 1100},
    {"nivel": 6, "titulo": "Voz Académica",        "emoji": "💼", "puntos_min": 1600},
    {"nivel": 7, "titulo": "Economista Principal", "emoji": "🏆", "puntos_min": 2500},
]

PUNTOS_ACCIONES = {
    "articulo_academico_aprobado": 30,
    "articulo_libre": 10,
    "like_recibido": 3,
    "comentario": 2,
    "top_semana": 40,
}

def calcular_nivel(puntos: int) -> int:
    nivel = 1
    for n in NIVELES:
        if puntos >= n["puntos_min"]:
            nivel = n["nivel"]
    return nivel


class Organizacion(Base):
    __tablename__ = "organizaciones"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), unique=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo = Column(String(100), nullable=True)
    activa = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    miembros = relationship("Usuario", back_populates="organizacion")
    articulos = relationship("Articulo", back_populates="organizacion")


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(String(20), default="estudiante", nullable=False)
    activo = Column(Boolean, default=True)
    email_verificado = Column(Boolean, default=False)
    codigo_verificacion = Column(String(10), nullable=True)
    codigo_expira = Column(DateTime(timezone=True), nullable=True)
    foto_perfil = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    tipo_usuario = Column(String(50), nullable=True)
    universidad = Column(String(200), nullable=True)
    facultad = Column(String(200), nullable=True)
    carrera = Column(String(100), nullable=True)
    semestre = Column(Integer, nullable=True)
    pais = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)
    areas_interes = Column(String(500), nullable=True)
    twitter = Column(String(100), nullable=True)
    linkedin = Column(String(200), nullable=True)
    email_publico = Column(String(150), nullable=True)
    sitio_web = Column(String(300), nullable=True)
    mostrar_email = Column(Boolean, default=False)
    mostrar_linkedin = Column(Boolean, default=True)
    mostrar_twitter = Column(Boolean, default=True)
    mostrar_universidad = Column(Boolean, default=True)
    mostrar_carrera = Column(Boolean, default=True)
    puntos = Column(Integer, default=0)
    nivel = Column(Integer, default=1)
    organizacion_id = Column(Integer, ForeignKey("organizaciones.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    organizacion = relationship("Organizacion", back_populates="miembros")
    articulos = relationship("Articulo", back_populates="autor", foreign_keys="Articulo.autor_id")
    comentarios = relationship("Comentario", back_populates="usuario")
    acciones = relationship("AccionAdmin", back_populates="admin", foreign_keys="AccionAdmin.admin_id")
    likes_articulos = relationship("Like", back_populates="usuario")
    likes_comentarios = relationship("LikeComentario", back_populates="usuario")
    puntos_historial = relationship("PuntosHistorial", back_populates="usuario")
    notificaciones = relationship("Notificacion", back_populates="usuario", foreign_keys="Notificacion.usuario_id")


class Articulo(Base):
    __tablename__ = "articulos"
    id = Column(Integer, primary_key=True, index=True)
    autor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    organizacion_id = Column(Integer, ForeignKey("organizaciones.id"), nullable=True)
    titulo = Column(String(255), nullable=False)
    resumen = Column(String(500), nullable=True)
    contenido_html = Column(Text, nullable=True)
    archivo_url = Column(String(500), nullable=True)
    tipo_archivo = Column(String(10), nullable=True)
    tipo_contenido = Column(String(10), nullable=False)
    imagen_portada = Column(String(500), nullable=True)
    zona = Column(String(10), nullable=False)
    estado = Column(String(15), default="pendiente", nullable=False)
    tags = Column(String(300), nullable=True)
    seccion = Column(String(100), nullable=True)
    vistas = Column(Integer, default=0)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    editado_en = Column(DateTime(timezone=True), nullable=True)
    autor = relationship("Usuario", back_populates="articulos", foreign_keys=[autor_id])
    organizacion = relationship("Organizacion", back_populates="articulos")
    comentarios = relationship("Comentario", back_populates="articulo")
    reportes = relationship("Reporte", back_populates="articulo")
    acciones = relationship("AccionAdmin", back_populates="articulo")
    likes = relationship("Like", back_populates="articulo")
    archivos = relationship("ArchivoArticulo", back_populates="articulo")


class ArchivoArticulo(Base):
    __tablename__ = "archivos_articulo"
    id = Column(Integer, primary_key=True, index=True)
    articulo_id = Column(Integer, ForeignKey("articulos.id"), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    nombre_guardado = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False)
    tamanio_kb = Column(Integer, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    articulo = relationship("Articulo", back_populates="archivos")


class Comentario(Base):
    __tablename__ = "comentarios"
    id = Column(Integer, primary_key=True, index=True)
    articulo_id = Column(Integer, ForeignKey("articulos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comentarios.id"), nullable=True)
    contenido = Column(Text, nullable=False)
    visible = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    articulo = relationship("Articulo", back_populates="comentarios")
    usuario = relationship("Usuario", back_populates="comentarios")
    respuestas = relationship("Comentario", backref="parent", remote_side=[id])
    likes = relationship("LikeComentario", back_populates="comentario")


class LikeComentario(Base):
    __tablename__ = "likes_comentarios"
    id = Column(Integer, primary_key=True, index=True)
    comentario_id = Column(Integer, ForeignKey("comentarios.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    comentario = relationship("Comentario", back_populates="likes")
    usuario = relationship("Usuario", back_populates="likes_comentarios")


class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    articulo_id = Column(Integer, ForeignKey("articulos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    ip_address = Column(String(50), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    articulo = relationship("Articulo", back_populates="likes")
    usuario = relationship("Usuario", back_populates="likes_articulos")


class Reporte(Base):
    __tablename__ = "reportes"
    id = Column(Integer, primary_key=True, index=True)
    articulo_id = Column(Integer, ForeignKey("articulos.id"), nullable=False)
    nombre_reportador = Column(String(100), nullable=False)
    email_reportador = Column(String(150), nullable=False)
    razon = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    revisado = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    articulo = relationship("Articulo", back_populates="reportes")


class PuntosHistorial(Base):
    __tablename__ = "puntos_historial"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    puntos = Column(Integer, nullable=False)
    razon = Column(String(200), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    usuario = relationship("Usuario", back_populates="puntos_historial")


class Notificacion(Base):
    __tablename__ = "notificaciones"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(String(50), nullable=False)
    mensaje = Column(String(300), nullable=False)
    link = Column(String(300), nullable=True)
    leida = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    usuario = relationship("Usuario", back_populates="notificaciones", foreign_keys=[usuario_id])


class MensajeContacto(Base):
    __tablename__ = "mensajes_contacto"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    asunto = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    imagen_url = Column(String(500), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    revisado = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class AccionAdmin(Base):
    __tablename__ = "acciones_admin"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    articulo_id = Column(Integer, ForeignKey("articulos.id"), nullable=True)
    usuario_afectado_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo_accion = Column(String(30), nullable=False)
    nota = Column(Text, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    admin = relationship("Usuario", back_populates="acciones", foreign_keys=[admin_id])
    articulo = relationship("Articulo", back_populates="acciones")
