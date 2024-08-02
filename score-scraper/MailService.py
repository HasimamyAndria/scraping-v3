import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class MailService:
    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password, from_addr, to_addr):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr
        self.to_addr = to_addr

    def handle_exception(self, establishment, ename, provider, exception, traceback_info):
        subject = f"Alerte d'erreur : Problème de scraping score"
        body = f"""
        <html>
        <body>
            <p>Bonjour,</p>
            <p>Une erreur s'est produite lors du processus de scraping pour l'établissement suivant :</p>
            <p><b>Établissement id :</b> {establishment} </p>
            <p><b>Nom de l'établissement  :</b> {ename} </p>
            <p><b>Provider :</b> {provider}</p>
            <p><b>Erreur :</b> {exception}</p>
            <p><b>Traceback :</b></p>
            <pre>{traceback_info}</pre>
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

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_addr, self.to_addr, msg.as_string())
