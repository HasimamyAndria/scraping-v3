import json
from os import path, environ
import dotenv
from datetime import datetime
from MailService import MailService

# Charger les variables d'environnement depuis le fichier .env
dotenv.load_dotenv()

class Scraping(object):
    def __init__(self, items: list) -> None:
        # Initialisation des attributs de la classe
        self.posts = []  # Liste pour stocker les posts collectés
        self.page_data = {}  # Dictionnaire pour stocker les données de la page
        self.items = items  # Liste des éléments à scraper
        self.establishment = ''  # Identifiant de l'établissement en cours
        self.url = ''  # URL à scraper
        self.current_credential = {}  # Informations d'identification actuelles
        self.env = 'DEV'  
        self.error_log_filename = f'{environ.get("ERROR_LOG_FOLDER")}/social-scraping-error-log.txt'  # Chemin du fichier de log des erreurs

        # Initialisation du service d'envoi d'e-mails
        self.mail_service = MailService(
            smtp_server="smtp.gmail.com",  
            smtp_port=587,  
            smtp_user="hasimamyandriamitantsoa@gmail.com",  
            smtp_password="irex ehtb aqil zglz",  
            from_addr="hasimamyandriamitantsoa@gmail.com",  
            to_addr="rakotonomenjanaharymario9@gmail.com"  
        )

    def set_environ(self, env):
        """Définit l'environnement d'exécution."""
        self.env = env

    def set_current_credential(self, index):
        """Définit les informations d'identification actuelles à partir de l'index donné."""
        self.current_credential = self.credentials[index]

    def set_credentials(self, source: str) -> None:
        """Charge les informations d'identification à partir du fichier logins.json pour la source spécifiée."""
        logins_path = path.join(path.dirname(__file__), 'logins.json')  
        with open(logins_path, 'r') as f:
            data = json.load(f)  
            self.credentials = data[source]  

        if len(self.credentials):
            self.set_current_credential(0)  

    def set_item(self, item):
        self.establishment = item['establishment_id']  
        self.url = item['url']  
        self.etab_name = item['establishment_name']  

    def save(self):
        """Sauvegarde les données de la page dans un fichier JSON."""
        try:
            page_data = self.page_data
            page_data['posts'] = self.posts  
            page_data['url'] = self.url  
            page_data['createdAt'] = datetime.now().strftime('%Y-%m-%d')  
            page_data['hasStat'] = "1"  

            e_name = page_data['name']  

            output_file = f"{self.env}_{self.establishment}_{e_name}_{datetime.now().strftime('%Y-%m-%d')}"

            # Sauvegarder les données de la page dans un fichier JSON
            with open(f"{environ.get('SOCIAL_FOLDER')}/{output_file}.json", 'w', encoding='utf-8') as foutput:
                json.dump(page_data, foutput, indent=4, sort_keys=True)

            # Réinitialiser les attributs de données pour la prochaine utilisation
            self.posts = []
            self.page_data = {}

            return output_file

        except Exception as e:
            # Gérer les erreurs de sauvegarde
            self.log_error(f"Error in save method: {e}")
            print("Erreur ici")
            print(e)

    def log_error(self, message: str) -> None:
        """Enregistre les erreurs dans un fichier de log et envoie une notification par e-mail."""
        now = datetime.now()
        # Formatage du message d'erreur
        error_message = (f"{now.strftime('%d/%m/%Y %H:%M:%S')} - "
                         f"Source: {self.__class__.__name__} - Ename: {self.establishment} - "
                         f"{message}\n")
        
        # Enregistrer le message d'erreur dans le fichier de log
        with open(self.error_log_filename, 'a', encoding='utf-8') as error_file:
            error_file.write(error_message)
        
        # Envoyer une notification par e-mail avec les détails de l'erreur
        self.mail_service.handle_exception(
            establishment=self.establishment,
            source=self.__class__.__name__,
            ename=self.etab_name,
            exception=error_message
        )   

    def stop(self):
        pass
