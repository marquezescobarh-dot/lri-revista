from sqlalchemy.orm import Session
import models

def dar_puntos(db: Session, usuario_id: int, puntos: int, razon: str):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        return
    usuario.puntos = max(0, (usuario.puntos or 0) + puntos)
    usuario.nivel = models.calcular_nivel(usuario.puntos)
    db.add(models.PuntosHistorial(usuario_id=usuario_id, puntos=puntos, razon=razon))
    db.commit()

def get_nivel_info(puntos: int) -> dict:
    nivel_actual = None
    nivel_siguiente = None
    for i, n in enumerate(models.NIVELES):
        if puntos >= n["puntos_min"]:
            nivel_actual = n
            nivel_siguiente = models.NIVELES[i + 1] if i + 1 < len(models.NIVELES) else None
    progreso = 0
    if nivel_actual and nivel_siguiente:
        rango = nivel_siguiente["puntos_min"] - nivel_actual["puntos_min"]
        avance = puntos - nivel_actual["puntos_min"]
        progreso = int((avance / rango) * 100)
    elif nivel_actual and not nivel_siguiente:
        progreso = 100
    return {
        "nivel_actual": nivel_actual,
        "nivel_siguiente": nivel_siguiente,
        "progreso_porcentaje": progreso,
        "puntos_para_siguiente": (nivel_siguiente["puntos_min"] - puntos) if nivel_siguiente else 0,
    }