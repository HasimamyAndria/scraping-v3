from models import Establishment, Settings
from booking import Booking
from maeva import Maeva
from campings import Campings
from hotels import Hotels_FR, Hotels_EN
from googles import Google, GoogleTravel
from opentable import Opentable, Opentable_UK
from trustpilot import Trustpilot
from tripadvisor import Tripadvisor, Tripadvisor_UK, Tripadvisor_FR, Tripadvisor_ES
from expedia import Expedia
from yelp import Yelp
from api import ERApi
import random
from changeip import refresh_connection
import time
from datetime import datetime
from thefork import Thefork
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
    'Booking ES': Booking,
    'Booking MU': Booking,
    'Maeva': Maeva,
    'Maeva ES': Maeva,
    'Campings': Campings,
    'Campings ES': Campings,
    'Hotels.com FR': Hotels_FR,
    'Hotels.com ES': Hotels_FR,
    'Google': Google,
    'Google hotel': Google,
    'Google Travel': GoogleTravel,
    'Opentable UK': Opentable_UK,
    'Opentable': Opentable,
    'Trustpilot': Trustpilot,
    'Tripadvisor FR': Tripadvisor_FR,
    'Tripadvisor UK': Tripadvisor_UK,
    'Tripadvisor ES': Tripadvisor_ES,
    'Tripadvisor': Tripadvisor,
    'Expedia': Expedia,
    'Expedia FR': Expedia,
    'Expedia ES': Expedia,
    'Thefork': Thefork,
    'Yelp': Yelp
}


class ListScraperV2:
    def __init__(self, env):
        self.settings = None
        self.last_date = None
        self.env = env
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
            #self.mail_service.handle_exception(e)
            return {}
            # print(e)

        return {
            "providers": list(map(lambda x: x['name'], res['providers'])),
            "establishments": res['establishments']
        }

    def init(self, eid=None, ename=None, categ=None, source=None):
        self.settings = Settings(categ, eid, source, ename, self.env)
        self.settings.prepare()

    def set_last_date(self, date):
        self.last_date = date

    def start(self):
        logging.info("Démarrage du scraping...")
        print("Liste des établissements à scraper:")
        print(
            list(map(lambda x: x['establishment_name'], self.settings.items)))

        for item in self.settings.items:
            time.sleep(random.randint(1, 3))
            # print(item)

            print(
                f"****** {item['establishment_name']} / {item['source']} ******")
            print(
                f"\t=> {item['url']}")

            if item['source'] in __class_name_v2__.keys():
                print("=> A scraper !!!")
                try:
                    instance = __class_name_v2__[item['source']](
                        url=item['url'], establishment=item['establishment_id'], establishment_name=item['establishment_name'],  env=self.env)
                    # print(item['url'])

            #         if item['last_review_date']:
            #             if self.last_date:
            #                 if datetime.strptime(self.last_date, "%d/%m/%Y") < datetime.strptime(item['last_review_date'], "%d/%m/%Y"):
            #                     instance.set_last_date(
            #                         item['last_review_date'])
            #                 else:
            #                     instance.set_last_date(self.last_date)
            #             else:
            #                 instance.set_last_date(item['last_review_date'])

                    instance.execute()
                except Exception as e:
                    #logging.error(f"Erreur lors du scraping de {item['establishment_name']}: {e}")
                    #self.mail_service.handle_exception(e)
                    

                    logging.error(f"Erreur lors du scraping de {item['establishment_name']}: {e}")
                    self.mail_service.handle_exception(item['establishment_id'],item['establishment_name'],item['source'], e, traceback.format_exc())
                    continue

            #     # if counter == 4:
            #     #     counter == 0
            #     #     refresh_connection()

            else:
                logging.warning(f"{item['source']} n'est pas dans la liste des sources supportées.")
        logging.info("Fin du scraping.")
