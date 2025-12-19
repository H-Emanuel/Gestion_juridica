import smtplib
from email.message import EmailMessage
from email.utils import formataddr


def enviar_correo_smtp(usuario,contraseña,asunto,cuerpo,destinatarios,cc=None,archivos=None):

    smtp_correo = f"{usuario}@munivalpo.cl"
    smtp_usuario = f"servervalpo\\{usuario}"
    smtp_contraseña = contraseña


    print( "Enviando correo SMTP..." )
    print(smtp_correo, smtp_usuario)
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

    with smtplib.SMTP("mail.munivalpo.cl", 587) as server:
        server.set_debuglevel(1)
        server.ehlo()
        server.starttls()
        server.ehlo()

        # ✅ Login correcto para AD / Exchange
        server.login(smtp_usuario, smtp_contraseña)
        server.send_message(msg)
