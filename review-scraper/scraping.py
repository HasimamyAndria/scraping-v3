from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from abc import abstractmethod
import sys
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from models import Review
import dotenv
import os
from changeip import refresh_connection
import random
import string
from pathlib import Path
from lingua import Language, LanguageDetectorBuilder
from MailService import MailService
import logging
import traceback

class Scraping(object):
    def __init__(self, in_background: bool, url: str, establishment: str, establishment_name: str,
                 source: str, settings: str, env: str, force_refresh=False) -> None:
        """Initialise les options du navigateur et les paramètres de scraping."""

        # Options pour le navigateur Chrome
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        if in_background:
            self.chrome_options.add_argument('--headless')  
        self.chrome_options.add_argument('--incognito')

        # Options pour le navigateur Firefox
        self.firefox_options = webdriver.FirefoxOptions()
        self.firefox_options.add_argument('--disable-gpu')
        self.firefox_options.add_argument('--ignore-certificate-errors')
        if in_background:
            self.firefox_options.add_argument('--headless')  
        self.firefox_options.add_argument('--incognito')
        self.firefox_options.set_preference('intl.accept_languages', 'en-US, en')
        
        self.force_refresh = force_refresh

        # Chargement des variables d'environnement
        dotenv.load_dotenv()

        # Initialisation du driver
        if os.environ.get('DRIVER') == 'chrome':
            self.chrome_options.add_extension(f'{Path(str(Path.cwd()) + "/canvas_blocker_0_2_0_0.crx")}')
            self.driver = webdriver.Chrome(options=self.chrome_options)
        else:
            self.driver = webdriver.Firefox(options=self.firefox_options)
            self.driver.install_addon(f'{Path(str(Path.cwd()) + "/canvasblocker-1.10.1.xpi")}')

        self.driver.maximize_window()

        self.data = {}
        self.url = url
        self.establishment = establishment
        self.establishment_name = establishment_name
        self.source = source
        self.settings = settings
        self.last_date = None
        self.env = env
        self.lang = 'fr'
        self.setting_id = "-1"

        self.set_random_params()

        # Initialisation du service de mail
        self.mail_service = MailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_user="hasimamyandriamitantsoa@gmail.com",
            smtp_password="irex ehtb aqil zglz",
            from_addr="hasimamyandriamitantsoa@gmail.com",
            to_addr="rakotonomenjanaharymario9@gmail.com"
        )

    def set_random_params(self):
        """Ajoute des paramètres aléatoires à l'URL pour éviter les mises en cache."""
        random_params = ""
        length = random.randint(1, 5)
        param_characters = string.ascii_letters
        value_characters = string.ascii_letters + string.digits

        for i in range(length):
            key_length = random.randint(1, 6)
            value_length = random.randint(2, 20)
            random_params += '&' + ''.join(random.choices(param_characters, k=key_length)) \
                + '=' + ''.join(random.choices(value_characters, k=value_length))

        self.url = self.url + '?' + random_params[1:] if self.url.endswith('.html') else self.url + random_params

    def detect(self, text: str) -> str:
        """Détecte la langue du texte donné."""
        if text:
            lang_code = {
                'Language.ENGLISH': 'en',
                'Language.GERMAN': 'de',
                'Language.SPANISH': 'es',
                'Language.FRENCH': 'fr',
            }

            languages = [Language.ENGLISH, Language.FRENCH, Language.GERMAN, Language.SPANISH]
            detector = LanguageDetectorBuilder.from_languages(*languages).build()
            try:
                return lang_code[f"{detector.detect_language_of(text)}"]
            except:
                return ''

    def set_setting_id(self, setting_id):
        self.setting_id = setting_id

    def set_last_date(self, date):
        self.last_date = datetime.strptime(date, '%d/%m/%Y')

    def set_establishment(self, establishment):
        self.establishment = establishment

    def set_url(self, url: str) -> None:
        self.url = url
        self.set_random_params()

    def set_language(self, language: str) -> None:
        """Définit la langue pour le scraping."""
        print("La langue du client: ", language.lower())
        self.lang = language.lower()

    def check_date(self, date) -> bool:
        """Vérifie si la date est passé."""
        current_date = datetime.strptime(date, '%d/%m/%Y')
        return current_date >= (current_date - timedelta(days=365))

    def execute(self):
        """Exécute le processus de scraping."""
        try:
            if self.force_refresh:
                refresh_connection()

            self.scrap()
            time.sleep(5)
            WebDriverWait(self.driver, 10)
            if self.check_page():
                self.extract()
                time.sleep(2)
                self.save()
            else:
                print("!!!!!!!! Cette page n'existe pas !!!!!!!!")
            self.driver.quit()
        except Exception as e:
            print(e)
            logging.error(f"Erreur lors de l'execution : {e}")
            traceback_info = traceback.format_exc()
            self.mail_service.handle_exception(self.establishment, self.establishment_name, self.source, e)
            self.driver.quit()
            sys.exit("Arret")

    def scrap(self) -> None:
        """Charge la page à scraper."""
        try:
            self.set_random_params()
            self.driver.get(self.url)
        except Exception as e:
            logging.error(f"Erreur lors du scrap : {e}")
            traceback_info = traceback.format_exc()
            self.mail_service.handle_exception(self.establishment, self.establishment_name, self.source, e)

    def refresh(self) -> None:
        """Rafraîchit la page actuelle du navigateur."""
        try:
            self.driver.refresh()
        except Exception as e:
            print(e)
            logging.error(f"Erreur lors du refresh : {e}")
            traceback_info = traceback.format_exc()
            self.mail_service.handle_exception(self.establishment, self.establishment_name, self.source, e)

    def exit(self) -> None:
        """Quitter le navigateur et termine le programme."""
        self.driver.quit()
        sys.exit("Arret")

    def check_page(self) -> None:
        """Vérifier si la page est valide. Méthode à remplacer par une logique spécifique selon les besoins."""
        return True

    def format(self) -> None:
        """Formate les données extraites pour les préparer à l'enregistrement."""
        column_order = ['author', 'source', 'language', 'rating', 'establishment', 'date_review', 'settings']

        def check_value(item):
            """Vérifie que toutes les valeurs requises sont présentes dans l'élément."""
            for key in column_order:
                if not item[key] or item[key] == '':
                    print("erreur: ", key)
                    return False
            return True

        result = ""

        for item in self.data:
            print(item)
            if check_value(item):
                line = '$$$$$'.join([item['author'], item['source'], item['language'], item['rating'], item['establishment'], item['date_review'],
                                    item['comment'].replace('$', 'USD'), item['settings'], item['date_visit'], item['novisitday'], item['url'] if 'url' in item.keys() else 'non']) + "#####"

                result += line

        self.formated_data = result

    def save(self) -> None:
        """Enregistre les données formatées dans la base."""
        try:
            self.format()

            if self.formated_data:
                print(self.formated_data)
                Review.save_multi(self.formated_data, self.env)
                print(len(self.data), "reviews uploaded!")
            else:
                print("No review uploaded!")

        except Exception as e:
            print(e)
            logging.error(f"Erreur lors du scrap : {e}")
            traceback_info = traceback.format_exc()
            self.mail_service.handle_exception(self.establishment, self.establishment_name, self.source, e)

    @abstractmethod
    def extract(self) -> None:
        pass
