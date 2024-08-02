from datetime import datetime
import json
import os
from twitter_spider import TwitterProfileScraper, TwitterProfileScraperFR, TwitterScraper, X_scraper
from models import Settings
from facebook_scraper import FacebookProfileScraper
from instagram_scraper import InstagramProfileScraper
from tiktok_spider import TikTokProfileScraper
from linkedIn_spider import LinkedInProfileScraper
from youtube_scraper import YoutubeProfileScraper
import random
from changeip import refresh_connection
import time
import pathlib
from api import ERApi
from progress.bar import ChargingBar
from MailService import MailService
from logging_config import setup_logging
import logging
import traceback

# Configuration logging 
setup_logging()

__class_name__ = {
    'Youtube': YoutubeProfileScraper,
    'Instagram': InstagramProfileScraper,
    'Linkedin': LinkedInProfileScraper,
    'facebook EN': FacebookProfileScraper,
    'Twitter': X_scraper,
    'Twitter (X)': X_scraper,
    'Tiktok': TikTokProfileScraper,
    'Facebook': FacebookProfileScraper
}

class ListScraper:
    def __init__(self, env: str):
        self.settings = None
        self.auto_save = False
        self.env = env
        self.error_log_filename = f'{os.environ.get("ERROR_LOG_FOLDER")}/social-scraping-error-log.txt'
        self.source_name = ''
        self.ename = ''

        # Initialisation du service mail
        self.mail_service = MailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_user="hasimamyandriamitantsoa@gmail.com",
            smtp_password="irex ehtb aqil zglz",
            from_addr="hasimamyandriamitantsoa@gmail.com",
            to_addr="rakotonomenjanaharymario9@gmail.com"
        )

    def log_error(self, message):
        """Enregistre un message d'erreur dans le fichier de log et envoie une notification par e-mail."""
        now = datetime.now()
        error_message = (f"{now.strftime('%d/%m/%Y %H:%M:%S')} - "
                         f"Source: {self.source_name} - Ename: {self.ename} - "
                         f"{message}\n")
        with open(self.error_log_filename, 'a', encoding='utf-8') as error_file:
            error_file.write(error_message)

        # Envoi d'une notification par e-mail avec les détails de l'erreur
        self.mail_service.handle_exception(
            establishment=self.ename,
            source=self.source_name,
            ename=self.ename,
            exception=error_message
        )

    def init(self, eid=None, ename=None, categ='Social', source=None):
        """Initialise les paramètres du scraper à partir des paramètres fournis."""
        try:
            # Préparation des paramètres de configuration pour le scraping
            self.settings = Settings(categ, eid, source, ename, env=self.env)
            self.settings.prepare()
            self.source_name = source
            self.ename = ename
        except Exception as e:
            # Enregistrement des erreurs survenues lors de l'initialisation
            self.log_error(f"Error initializing settings: {e}")
            raise

    def set_auto_save(self):
        """Active la sauvegarde automatique des données après le scraping."""
        self.auto_save = True

    def get_providers(self):
        """Récupère la liste des fournisseurs et des établissements à partir de l'API."""
        try:
            res = ERApi(entity='provider/list?categ=Social', env=self.env).execute()
            return {
                "providers": list(map(lambda x: x['name'], res['providers'])),
                "establishments": res['establishments']
            }
        except Exception as e:
            # Enregistrement des erreurs survenues lors de la récupération des fournisseurs
            self.log_error(f"Error getting providers: {e}")
            raise

    def start(self):
        """Démarre le processus de scraping pour tous les fournisseurs."""
        try:
            refresh_connection()
            counter = 0
            by_source = {}

            # Affichage des éléments à scraper
            print(self.settings.items)

            # Regroupement des éléments par source(Provider)
            for source in __class_name__.keys():
                by_source[source] = [
                    item for item in self.settings.items if item['source'] == source]

            for item_key in by_source.keys():
                time.sleep(random.randint(1, 3))  # Pause entre les requêtes
                if item_key in __class_name__.keys() and len(by_source[item_key]):
                    try:
                        # Création d'une instance du scraper pour la source actuelle
                        instance = __class_name__[item_key](items=by_source[item_key])
                        files = instance.execute()

                        print("After execute...")

                        if self.auto_save:
                            print("Transform and upload ...")
                            for f in files:
                                self.transform_data(filename=f)
                                self.upload_data(file=f)

                    except Exception as e:
                        # Enregistrement des erreurs survenues pendant le traitement
                        self.log_error(f"Error processing {item_key}: {e}")

        except Exception as e:
            # Enregistrement des erreurs survenues lors du démarrage du scraper
            self.log_error(f"Error starting scraper: {e}")
            raise

    def transform_all_data(self):
        """Transforme toutes les données des fichiers JSON dans le dossier spécifié."""
        try:
            files = [pathlib.Path(f).stem for f in os.listdir(os.environ.get(
                'SOCIAL_FOLDER')) if pathlib.Path(f).suffix == '.json']
            for file in files:
                self.transform_data(file)
        except Exception as e:
            # Enregistrement des erreurs survenues lors de la transformation des données
            self.log_error(f"Error transforming all data: {e}")
            raise

    def transform_data(self, filename):
        results = ""
        try:
            with open(f"{os.environ.get('SOCIAL_FOLDER')}/{filename}.json", 'r', encoding='utf-8') as finput:
                data = json.load(finput, strict=False)

            for item in data['posts']:
                if "publishedAt" in item.keys():
                    item['uploadAt'] = item['publishedAt']
                    del item['publishedAt']
                    try:
                        item['uploadAt'] = datetime.strptime(
                            item['uploadAt'], '%d/%m/%Y').strftime('%Y-%m-%d')
                    except Exception:
                        try:
                            item['uploadAt'] = datetime.strptime(
                                item['uploadAt'], '%d-%m-%Y').strftime('%Y-%m-%d')
                        except:
                            pass

                if "description" in item.keys():
                    item['title'] = item['description']

                if "reaction" in item.keys():
                    item['likes'] = item['reaction']

                if "shares" in item.keys():
                    item['share'] = item['shares']

                comments = ""

                for com in item['comment_values']:
                    comments += '|cc|'.join(
                        [com['comment'], com['author'], str(com['likes']), datetime.strptime(
                            com['published_at'], '%d/%m/%Y').strftime('%Y-%m-%d')]) + "|cl|"

                line = '|&|'.join([item['author'], item['title'], item['uploadAt'],
                                   str(item['likes']), str(item['share']), str(item['comments']), item['hashtag'], comments]) + "|*|"

                if len(line.split('|&|')) == 8:
                    results += line

            with open(f"{os.environ.get('SOCIAL_FOLDER')}/uploads/{filename}.txt", 'w', encoding='utf-8') as foutput:
                foutput.write(results)

            with open(f"{os.environ.get('SOCIAL_FOLDER')}/uploads/{filename}.json", 'w') as foutput:
                json.dump(data, foutput, indent=4, sort_keys=True)

        except Exception as e:
            # Enregistrement des erreurs survenues lors de la transformation des données
            self.log_error(f"Error transforming data for {filename}: {e}")
            print(e)

    def upload_data(self, file):
        """Télécharge les données transformées vers l'API."""
        try:
            data = {}
            posts = ""

            with open(f"{os.environ.get('SOCIAL_FOLDER')}/uploads/{file}.json", 'r') as dinput:
                data = json.load(dinput)
                data['posts'] = len(data['posts'])
                del data['url']

            with open(f"{os.environ.get('SOCIAL_FOLDER')}/uploads/{file}.txt", 'r', encoding='utf-8') as pinput:
                for line in pinput.readlines():
                    posts += " " + line.strip()

            data['post_items'] = posts

            post = ERApi(method='postmulti', env=self.env)
            post.set_body(data)

            result = post.execute()
            print(result.text)

        except Exception as e:
            # Enregistrement des erreurs survenues lors du téléchargement des données
            self.log_error(f"Error uploading data for {file}: {e}")
            raise

    def upload_all_results(self):
        """Télécharge tous les résultats transformés vers l'API."""
        try:
            files = [pathlib.Path(f).stem for f in os.listdir(
                f"{os.environ.get('SOCIAL_FOLDER')}/uploads") if pathlib.Path(f).suffix == '.json']
            progress = ChargingBar('Processing ', max=len(files))
            for file in files:
                self.upload_data(file)
                progress.next()
                print(" | ", file)
            progress.finish()
        except Exception as e:
            # Enregistrement des erreurs survenues lors du téléchargement de tous les résultats
            self.log_error(f"Error uploading all results: {e}")
            raise
