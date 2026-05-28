from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import models, auth, os, httpx
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

router = APIRouter(prefix="/ia", tags=["IA"])


class ArticuloRevisar(BaseModel):
    titulo: str
    resumen: Optional[str] = ""
    contenido: Optional[str] = ""


@router.post("/revisar-articulo")
async def revisar_articulo(
    datos: ArticuloRevisar,
    admin: models.Usuario = Depends(auth.requerir_admin)
):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="IA no configurada")

    prompt = (
        "Eres un editor académico de una revista universitaria. "
        "Revisa el siguiente artículo y detecta si contiene:\n"
        "- Lenguaje de odio o discriminación\n"
        "- Palabras ofensivas o soeces\n"
        "- Contenido inapropiado para una revista académica\n"
        "- Insultos o ataques personales\n\n"
        f"TÍTULO: {datos.titulo}\n"
        f"RESUMEN: {datos.resumen or '(sin resumen)'}\n"
        f"CONTENIDO: {datos.contenido[:800] if datos.contenido else '(sin contenido)'}\n\n"
        "Responde SOLO en este formato exacto:\n\n"
        "RESULTADO: [APROBADO o REQUIERE REVISION]\n\n"
        "PROBLEMAS DETECTADOS:\n"
        "- [problema 1 o 'Ninguno']\n\n"
        "RECOMENDACION:\n"
        "[Una oración con tu recomendación para el editor]"
    )

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.3
                },
                timeout=15.0
            )
            res.raise_for_status()
            texto = res.json()["choices"][0]["message"]["content"]
            aprobado = "APROBADO" in texto.upper() and "REQUIERE" not in texto.upper()
            return {"revision": texto, "aprobado": aprobado}
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="La IA tardó demasiado, intenta de nuevo")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error IA: {str(e)}")
