import smtplib
import socket
from email.message import EmailMessage
from email.utils import formataddr

def enviar_correo_smtp(usuario, contraseña, asunto, cuerpo, destinatarios, cc=None, archivos=None):
    smtp_correo = f"{usuario}@munivalpo.cl"
    smtp_usuario = f"servervalpo\\{usuario}"

    msg = EmailMessage()
    msg["From"] = formataddr(("Municipalidad de Valparaíso", smtp_correo))
    msg["To"] = ", ".join(destinatarios)
    if cc:
        msg["Cc"] = ", ".join(cc)

    msg["Subject"] = asunto
    msg.set_content(cuerpo)

    if archivos:
        for archivo in archivos:
            archivo.seek(0)
            msg.add_attachment(
                archivo.read(),
                maintype="application",
                subtype="octet-stream",
                filename=archivo.name
            )

    try:
        # timeout evita que el worker quede colgado
        with smtplib.SMTP("mail.munivalpo.cl", 587, timeout=20) as server:
            # NO debug en prod (evita ruido + fugas)
            # server.set_debuglevel(1)

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(smtp_usuario, contraseña)
            server.send_message(msg)

    except (smtplib.SMTPException, socket.timeout, OSError) as e:
        # No tumbar gunicorn: sube un error manejable
        raise Exception(f"Error enviando correo SMTP: {e}")
