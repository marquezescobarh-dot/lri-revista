from database import SessionLocal, engine
import models
from auth import hashear_password
import getpass

def crear_superadmin():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("\n=== Crear Superadmin — La Riqueza de las Ideas ===\n")
    email = input("Email: ").strip()
    nombre = input("Nombre: ").strip()
    contrasena = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    if len(contrasena) < 8:
        print("Error: contraseña muy corta")
        return
    if db.query(models.Usuario).filter(models.Usuario.email == email).first():
        print(f"Error: ya existe una cuenta con {email}")
        db.close()
        return
    superadmin = models.Usuario(
        nombre=nombre, email=email,
        contrasena_hash=hashear_password(contrasena),
        rol="superadmin", activo=True, email_verificado=True,
        puntos=0, nivel=1
    )
    db.add(superadmin)
    db.commit()
    db.close()
    print(f"\nSuperadmin creado: {nombre} ({email})\n")

if __name__ == "__main__":
    crear_superadmin()