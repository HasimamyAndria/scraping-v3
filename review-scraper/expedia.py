from scraping import Scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.command import Command
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from abc import abstractmethod
import sys
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from langdetect import detect
import random
from tools import month_number


class Expedia(Scraping):
    def __init__(self, url: str, establishment: str,establishment_name: str,source: str, settings: str, env: str):
        url_split = url.split('.')
        url_split[-1] = 'Avis-Voyageurs'
        url = '.'.join(url_split)

        super().__init__(in_background=False, url=url,
                         establishment=establishment,establishment_name=establishment_name,source=source, settings=settings, env=env)

    def load_reviews(self):
        # time.sleep(5)
        print("\n Loading ... \n")

        def get_last_review_date():
            page = self.driver.page_source
            soupe = BeautifulSoup(page, 'lxml')
            last_review_cards = soupe.find(
                'div', {'id': 'app-layer-reviews-property-reviews-2330890'}).find_all('article', {'itemprop': 'review'})[-1]
            return self.find_review_date(last_review_cards)

        while True:
            time.sleep(random.randint(1, 3))

            if not self.check_date(get_last_review_date()):
                break

            try:
                next_btn = self.driver.find_elements(
                    By.CSS_SELECTOR, '.uitk-button.uitk-button-medium.uitk-button-has-text.uitk-button-secondary')

                if len(next_btn) == 2:
                    self.driver.execute_script(
                        "arguments[0].click();", next_btn[1])
                    time.sleep(random.randint(1, 3))
                else:
                    break

            except Exception as e:
                break

    def find_review_date(self, card):
        date_raw = card.find('span', {'itemprop': 'datePublished'}).text.strip(
        ) if card.find('span', {'itemprop': 'datePublished'}) else ""
        try:
            date_review = datetime.strftime(datetime.strptime(
                date_raw, '%b %d, %Y'), '%d/%m/%Y') if date_raw else "01/01/1999"
        except:
            date_rawt = date_raw.split()
            date_review = "%s/%s/%s" % (date_rawt[0], month_number(
                date_rawt[1], 'fr', 'short'), date_rawt[2])

        return date_review

    def extract(self):

        enter_key = str(input("Entrer un caractère svp:"))

        if enter_key:

            self.load_reviews()

            reviews = []

            print("\n Extraction ... \n")

            page = self.driver.page_source

            soupe = BeautifulSoup(page, 'lxml')

            review_cards = soupe.find('div', {
                                      'id': 'app-layer-reviews-property-reviews-2330890'}).find_all('article', {'itemprop': 'review'})
            for card in review_cards:
                title = card.find('span', {'itemprop': 'name'}).text.strip(
                ) if card.find('span', {'itemprop': 'name'}) else ""
                detail = card.find('span', {'itemprop': 'description'}).text.strip(
                ) if card.find('span', {'itemprop': 'description'}) else ""
                comment = f"{title}{': ' if title and detail else ''}{detail}"

                try:
                    lang = detect(comment)
                except:
                    lang = 'en'

                date_review = self.find_review_date(card)

                try:
                    t = {
                        'comment': comment,
                        'rating': card.find('span', {'itemprop': 'ratingValue'}).text.strip().split('/')[0] + "/10"
                        if card.find('span', {'itemprop': 'ratingValue'}) else "0/10",
                        'date_review': date_review,
                        'language': lang,
                        'source': urlparse(self.url).netloc.split('.')[1],
                        'author': card.find('h4').text.strip(),
                        'establishment': f'/api/establishments/{self.establishment}',
                        'settings': f'/api/settings/{self.settings}',
                        'date_visit': date_review,
                        'novisitday': "0"
                    }
                    t['date_review'] != '01/01/1999' and reviews.append(t)
                except Exception as e:
                    print(e)

            self.data = reviews


# trp = Expedia(url="https://www.expedia.com/Les-Deserts-Hotels-Vacanceole-Les-Balcons-DAix.h2481279.Hotel-Reviews")
# trp.execute()
# print(trp.data)
