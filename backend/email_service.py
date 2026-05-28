import smtplib, random, string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def generar_codigo():
    return ''.join(random.choices(string.digits, k=6))

def codigo_expiracion():
    return datetime.utcnow() + timedelta(minutes=15)

def _enviar_html(para, asunto, html):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        import re
        codigos = re.findall(r'letter-spacing:8px[^>]*>(\d{6})<', html)
        print(f"\n[DEV] Para: {para}")
        print(f"[DEV] Asunto: {asunto}")
        if codigos:
            print(f"[DEV] Codigo: {codigos[0]}")
        print()
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = "La Riqueza de las Ideas <" + SMTP_EMAIL + ">"
        msg["To"] = para
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, para, msg.as_string())
    except Exception as e:
        print("[EMAIL ERROR]", e)

def _base_html(contenido):
    return (
        "<!DOCTYPE html><html><body style=\"font-family:Georgia,serif;background:#FAFAF7;margin:0;padding:2rem\">"
        "<div style=\"max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;border:1.5px solid #DDD9CF\">"
        "<div style=\"background:#003580;padding:2rem;text-align:center\">"
        "<h1 style=\"color:#C9963A;font-size:1.8rem;margin:0;letter-spacing:2px\">LRI</h1>"
        "<p style=\"color:rgba(255,255,255,0.7);font-size:0.8rem;margin:0.3rem 0 0\">La Riqueza de las Ideas - UNAM</p>"
        "</div>"
        "<div style=\"padding:2rem\">" + contenido + "</div>"
        "<div style=\"background:#003580;padding:1rem 2rem;text-align:center\">"
        "<p style=\"color:rgba(255,255,255,0.5);font-size:0.75rem;margin:0\">2026 La Riqueza de las Ideas - Facultad de Economia, UNAM</p>"
        "</div></div></body></html>"
    )

def _bloque_codigo(codigo):
    return (
        "<div style=\"background:#E8EFF9;border:2px solid #003580;border-radius:12px;padding:1.5rem;text-align:center;margin:1.5rem 0\">"
        "<span style=\"font-family:monospace;font-size:2.5rem;font-weight:700;color:#003580;letter-spacing:8px\">" + codigo + "</span>"
        "</div>"
        "<p style=\"color:#9E9890;font-size:0.82rem;text-align:center\">Expira en <strong>15 minutos</strong>.</p>"
    )

def enviar_email_verificacion(email, nombre, codigo):
    contenido = (
        "<h2 style=\"color:#1A1A1A\">Hola, " + nombre + "</h2>"
        "<p style=\"color:#6B6560;line-height:1.7\">Tu codigo de verificacion para activar tu cuenta es:</p>"
        + _bloque_codigo(codigo)
    )
    _enviar_html(email, "Verifica tu cuenta LRI: " + codigo, _base_html(contenido))

def enviar_recuperacion(email, nombre, codigo):
    contenido = (
        "<h2 style=\"color:#1A1A1A\">Recuperar contrasena</h2>"
        "<p style=\"color:#6B6560;line-height:1.7\">Hola <strong>" + nombre + "</strong>, tu codigo para restablecer tu contrasena es:</p>"
        + _bloque_codigo(codigo)
        + "<p style=\"color:#9E9890;font-size:0.82rem\">Si no solicitaste esto, ignora este mensaje.</p>"
    )
    _enviar_html(email, "Recuperar contrasena LRI: " + codigo, _base_html(contenido))
