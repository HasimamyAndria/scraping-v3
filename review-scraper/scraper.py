from models import Establishment, Settings
from booking import Booking, Booking_ES
from maeva import Maeva
from campings import Campings
from hotels import Hotels_FR, Hotels_EN, Hotels_ES
from googles import Google
from opentable import Opentable, Opentable_UK
from trustpilot import Trustpilot
from tripadvisor import Tripadvisor_UK, Tripadvisor_FR, Tripadvisor_ES
from expedia import Expedia
from api import ERApi
import random
from changeip import refresh_connection
import time
from datetime import datetime
from tools import ReviewScore
from MailService import MailService
from logging_config import setup_logging
import logging
import traceback

def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

setup_logging()

__class_name__ = {
    'booking': Booking,
    'Booking ES': Booking,
    'Booking MU': Booking,
    'maeva': Maeva,
    'camping': Campings,
    'hotels_com': Hotels_FR,
    'google': Google,
    'opentable': Opentable,
    'trustpilot': Trustpilot,
    'tripadvisor': Tripadvisor_UK,
    'expedia': Expedia
}

__class_name_v2__ = {
    'Booking': Booking,
    'Booking ES': Booking_ES,
    'Booking MU': Booking,
    'Maeva': Maeva,
    'Maeva ES': Maeva,
    'Campings': Campings,
    'Campings ES': Campings,
    'Hotels.com FR': Hotels_FR,
    'Hotels.com ES': Hotels_ES,
    'Google': Google,
    'Google hotel': Google,
    'Google Travel': Google,
    'Opentable UK': Opentable_UK,
    'Opentable': Opentable,
    'Trustpilot': Trustpilot,
    'Tripadvisor FR': Tripadvisor_FR,
    'Tripadvisor UK': Tripadvisor_FR,
    'Tripadvisor ES': Tripadvisor_FR,
    'Expedia': Expedia,
    'Expedia FR': Expedia,
    'Expedia ES': Expedia,
}


class ListScraper:
    def __init__(self,):
        self.establishments = []
        self.ids = []

    def init(self, establishments=[]):
        instance = ERApi(entity="establishment/name", env="PROD")
        etabs = instance.execute()
        if len(establishments):
            self.ids = list(map(lambda y: y, list(
                filter(lambda x: x['name'] in establishments, etabs))))
        else:
            self.ids = list(
                map(lambda x: x, etabs))

        for item in self.ids:
            print("Récupération information des établissements: ",
                  self.ids.index(item)+1, '/', len(self.ids))
            etab = Establishment(rid=item['id'], name=item['name'])
            etab.set_tag(item['tag'])
            etab.refresh()
            self.establishments.append(etab)

    def start(self, websites=[]):
        refresh_connection()

        counter = 0

        for item in self.establishments:
            time.sleep(random.randint(1, 5))

            print("****** Establishment: ", item.name, " ******")

            for site in item.websites.keys():
                if site in websites:
                    if site in __class_name__.keys():
                        print("===>\t", site)
                        instance = __class_name__[site](
                            url=item.websites[site], establishment=item.id)
                        instance.execute()
                        print("\n\n")
                        counter += 1

                        if counter == 4:
                            counter == 0
                            refresh_connection()


class ListScraperV2:
    def __init__(self, env):
        self.settings = None
        self.last_date = None
        self.env = env
         # Info mail
        self.mail_service = MailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_user="hasimamyandriamitantsoa@gmail.com",
            smtp_password="irex ehtb aqil zglz",
            from_addr="hasimamyandriamitantsoa@gmail.com",
            to_addr="rakotonomenjanaharymario9@gmail.com"
        )
        print(self.env)

    def get_providers(self):
        try:
            res = ERApi(entity='provider/list?categ=Platform',
                        env=self.env).execute()
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des fournisseurs: {e}")
            self.mail_service.handle_exception("N/A", "N/A" ,"N/A", e, traceback.format_exc())
            print(e)

        return {
            "providers": list(map(lambda x: x['name'], res['providers'])),
            "establishments": res['establishments']
        }
    
    def init(self, eid=None, ename=None, categ=None, source=None):
        try:
            self.settings = Settings(categ, eid, source, ename, self.env)
            self.settings.prepare()
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation des paramètres: {e}")
            self.mail_service.handle_exception("N/A", "N/A", "N/A", e, traceback.format_exc())
            print(e)
    
    def get_comments(self, page):
        try:  
            commentsApi = ERApi(entity='review/feeling_null',
                                params={'page': page, 'limit': 50}, env=self.env)
            return commentsApi.execute()['data']
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des commentaires: {e}")
            self.mail_service.handle_exception("N/A", "N/A", "N/A", e, traceback.format_exc())
            print(e)
            return []
        
    def compute_scores(self, comments):
        review_score = ReviewScore()

        def set_score(item):
            try:
                score_data = review_score.compute_score(
                    item['comment'], item['language'], item['rating'], item['source'])

                item['feeling'] = score_data['feeling']
                item['score'] = score_data['score']
                item['confidence'] = score_data['confidence']
            except Exception as e:
                logging.error(f"Erreur lors du calcul des scores: {e}")
                self.mail_service.handle_exception("N/A", "N/A", "N/A", e, traceback.format_exc())
                print(e)    

            return item

        return list(map(lambda x: set_score(x), comments))

    def upload_feelings(self, comments):
        data = ""
        for item in comments:
            line = '&'.join([str(item['id']), str(item['feeling']),
                            str(item['score']), str(item['confidence'])]) + "#"
            if len(line.split('&')) == 4:
                data += line

        print(data)

        try:
            req = ERApi(method="patchscores", entity=f"review/update", env=self.env)
            req.set_body({'data_content': data})
            res = req.execute()
            print(res.status_code)
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour des feelings: {e}")
            self.mail_service.handle_exception("N/A", "N/A", "N/A", e)
            print(e)

    def update_feelings(self):
        # 1- Récupérer la liste des commentaires non calculés par 50
        # 2- calculer les feelings ... de ces commentaires
        # 3- upload les nouvelles valeurs
        # 4- Revenir à 1 tant que liste != liste vide

        page = 1
        while True:
            try:
                comments = self.get_comments(page)

                if len(comments) == 0:
                    break

                new_comments = self.compute_scores(comments)
                # print(new_comments)
                self.upload_feelings(new_comments)
                page += 1

            except Exception as e:
                logging.error(f"Erreur lors de la mise à jour des feelings: {e}")
                self.mail_service.handle_exception("N/A", "N/A", "N/A", e)

                print(e)
                break

    def set_last_date(self, date):
        self.last_date = date

    def start(self):
        # refresh_connection()

        # counter = 0
        print("Liste des établissements à scraper:")
        print(
            list(map(lambda x: x['establishment_name'], self.settings.items)))

        order = random.sample(
            range(len(self.settings.items)), len(self.settings.items))

        # for item in self.settings.items:
        for index in order:
            time.sleep(random.randint(1, 5))
            item = self.settings.items[index]

            print(
                f"******({index}) {item['establishment_name']} / {item['source']} ******")

            if item['source'] in __class_name_v2__.keys():
                print("=> A scraper !!!")
                try:
                    print(item['url'])
                    instance = __class_name_v2__[item['source']](
                        url=item['url'], establishment=item['establishment_id'],establishment_name=item['establishment_name'], source=item['source'], settings=item['id'], env=self.env)
                    item['language'] and instance.set_language(
                        item['language'])
                    instance.set_setting_id(item['id'])

                    instance.set_url(item['url'])

                    print('=> ', item['id'], ': ', item['url'])

                    if item['last_review_date']:
                        if self.last_date:
                            if datetime.strptime(self.last_date, "%d/%m/%Y") < datetime.strptime(item['last_review_date'], "%d/%m/%Y"):
                                instance.set_last_date(
                                    item['last_review_date'])
                            else:
                                instance.set_last_date(self.last_date)
                        else:
                            instance.set_last_date(item['last_review_date'])

                    instance.execute()
                except Exception as e:
                    logging.error(f"Erreur lors du scraping de {item['establishment_name']}: {e}")
                    self.mail_service.handle_exception(item['establishment_id'], item['establishment_name'],item['source'], e)
                    print(e)
                    pass

                # if counter == 4:
                #     counter == 0
                #     refresh_connection()

            else:
                logging.warning(f"!!!!!!!!! {item['source']} n'est pas dans la liste !!!!!!!!!!")
                # print(
                #     f"!!!!!!!!! {item['source']} n'as dans la liste !!!!!!!!!!")
