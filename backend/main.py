from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
import models, os

models.Base.metadata.create_all(bind=engine)
for folder in ["uploads/articulos","uploads/portadas","uploads/extras","uploads/editor","uploads/avatars","uploads/contacto"]:
    os.makedirs(folder, exist_ok=True)

app = FastAPI(title="La Riqueza de las Ideas", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from routers import auth_router, articulos_router, comentarios_router, admin_router, likes_router, buscar_router, organizaciones_router, perfil_router, notificaciones_router, contacto_router
app.include_router(auth_router.router)
app.include_router(articulos_router.router)
app.include_router(comentarios_router.router)
app.include_router(admin_router.router)
app.include_router(likes_router.router)
app.include_router(buscar_router.router)
app.include_router(organizaciones_router.router)
app.include_router(perfil_router.router)
app.include_router(notificaciones_router.router)
app.include_router(contacto_router.router)

@app.get("/")
def inicio():
    return {"mensaje": "La Riqueza de las Ideas — API v1.0"}
