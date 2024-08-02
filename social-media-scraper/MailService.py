import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging


class MailService:
    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password, from_addr, to_addr):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr
        self.to_addr = to_addr

    def handle_exception(self, establishment, source, ename,  exception):
        print("handle_exception called")  # Log to ensure the method is called
        subject = f"Alerte d'erreur : Problème de scraping social : {ename} / {source}"
        body = f"""
        <html>
        <body>
            <p>Bonjour,</p>
            <p>Une erreur s'est produite lors du processus de scraping pour l'établissement suivant :</p>
            <p><b>Établissement id :</b> {establishment} </p>
            <p><b>Provider  :</b> {source} </p>
            <p><b>Nom de l'établissement  :</b> {ename} </p>
            <p><b>Erreur(s) :</b></p>
            <pre> {exception}</pre>
            <p>Merci de bien vouloir résoudre ce problème dès que possible.</p>
            <p>Cordialement,<br>L'equipe de scraping</p>
        </body>
        </html>
        """
        
        self.send_email(subject, body)

    def send_email(self, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_addr, self.to_addr, msg.as_string())
            logging.info("Email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
