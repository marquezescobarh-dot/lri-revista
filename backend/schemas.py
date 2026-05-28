from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


class OrganizacionCrear(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo: Optional[str] = None

class OrganizacionPublica(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    tipo: Optional[str]
    creado_en: datetime
    class Config:
        from_attributes = True


class UsuarioRegistro(BaseModel):
    nombre: str
    email: EmailStr
    contrasena: str

    @field_validator("contrasena")
    def contrasena_segura(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

    @field_validator("nombre")
    def nombre_valido(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("El nombre es muy corto")
        return v.strip()

class UsuarioLogin(BaseModel):
    email: EmailStr
    contrasena: str
    recordarme: bool = False

class VerificarEmail(BaseModel):
    email: EmailStr
    codigo: str

class UsuarioPublico(BaseModel):
    id: int
    nombre: str
    carrera: Optional[str]
    universidad: Optional[str]
    foto_perfil: Optional[str]
    nivel: Optional[int]
    rol: str
    organizacion: Optional[OrganizacionPublica]
    creado_en: datetime
    class Config:
        from_attributes = True

class UsuarioConEmail(UsuarioPublico):
    email: str
    email_verificado: bool
    semestre: Optional[int]
    puntos: Optional[int]


class ArchivoPublico(BaseModel):
    id: int
    nombre_original: str
    nombre_guardado: str
    tipo: str
    tamanio_kb: Optional[int]
    class Config:
        from_attributes = True


class ArticuloCrear(BaseModel):
    titulo: str
    resumen: Optional[str] = None
    contenido_html: Optional[str] = None
    zona: str
    tags: Optional[str] = None
    seccion: Optional[str] = None

    @field_validator("zona")
    def zona_valida(cls, v):
        if v not in ("academico", "libre"):
            raise ValueError("Zona inválida")
        return v

    @field_validator("titulo")
    def titulo_valido(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("El título es muy corto")
        return v.strip()

class ArticuloPublico(BaseModel):
    id: int
    titulo: str
    resumen: Optional[str]
    contenido_html: Optional[str]
    archivo_url: Optional[str]
    tipo_archivo: Optional[str]
    tipo_contenido: str
    imagen_portada: Optional[str]
    zona: str
    estado: str
    tags: Optional[str]
    seccion: Optional[str]
    vistas: Optional[int]
    creado_en: datetime
    editado_en: Optional[datetime]
    autor: UsuarioPublico
    organizacion: Optional[OrganizacionPublica]
    archivos: List[ArchivoPublico] = []
    class Config:
        from_attributes = True

class ArticuloLista(BaseModel):
    id: int
    titulo: str
    resumen: Optional[str]
    zona: str
    estado: str
    tipo_contenido: str
    imagen_portada: Optional[str]
    tags: Optional[str]
    seccion: Optional[str]
    creado_en: datetime
    editado_en: Optional[datetime]
    autor: UsuarioPublico
    organizacion: Optional[OrganizacionPublica]
    class Config:
        from_attributes = True


class ComentarioCrear(BaseModel):
    contenido: str

    @field_validator("contenido")
    def contenido_valido(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("El comentario está vacío")
        if len(v) > 1000:
            raise ValueError("Máximo 1000 caracteres")
        return v.strip()

class ReporteCrear(BaseModel):
    nombre_reportador: str
    email_reportador: EmailStr
    razon: str
    descripcion: Optional[str] = None

    @field_validator("razon")
    def razon_valida(cls, v):
        if v not in ["contenido_inapropiado", "desinformacion", "plagio", "spam", "otro"]:
            raise ValueError("Razón no válida")
        return v

class AccionAdminCrear(BaseModel):
    tipo_accion: str
    nota: Optional[str] = None

class CambiarRol(BaseModel):
    usuario_id: int
    nuevo_rol: str

    @field_validator("nuevo_rol")
    def rol_valido(cls, v):
        if v not in ("estudiante", "admin"):
            raise ValueError("Rol inválido")
        return v

class Mensaje(BaseModel):
    mensaje: str

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioConEmail