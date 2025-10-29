from fastapi import HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_CONFIG
from database import get_pool

def send_email_via_smtp(subject: str, body: str, to_email: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_CONFIG["SENDER_EMAIL"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_CONFIG["SMTP_SERVER"], SMTP_CONFIG["SMTP_PORT"]) as server:
            server.starttls()
            server.login(SMTP_CONFIG["SENDER_EMAIL"], SMTP_CONFIG["SENDER_PASSWORD"])
            server.send_message(msg)

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Error de autenticación SMTP. Verifique las credenciales o la configuración de seguridad del remitente.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fallo al enviar el correo: {e}",
        )


def send_user_password_email(user_email: str, full_name: str, username: str, generated_password: str):
    subject = "Tu acceso al portal"
    body = (
        f"Hola {full_name}.\n\n"
        f"Tu cuenta ha sido creada correctamente.\n\n"
        f"Usuario: {username}\n"
        f"Contraseña: {generated_password}\n\n"
        "Saludos,\nEl equipo de soporte."
    )
    send_email_via_smtp(subject, body, user_email)

def send_new_password_email(user_email: str, full_name: str, username: str, generated_password: str):
    subject = "Tu nueva contraseña"
    body = (
        f"Hola {full_name}.\n\n"
        f"Tu contraseña ha sido actualizada correctamente.\n\n"
        f"Usuario: {username}\n"
        f"Nueva contraseña: {generated_password}\n\n"
        "Saludos,\nEl equipo de soporte."
    )
    send_email_via_smtp(subject, body, user_email)

async def update_sent_mail(user: str, status: bool):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            query = "SELECT fn_update_sent_mail($1, $2);"
            await conn.execute(query, user, status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en BD: {e}")
