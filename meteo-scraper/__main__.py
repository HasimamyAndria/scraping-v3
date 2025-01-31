import csv
import urllib3
import json
import pandas as pd
from datetime import datetime, timedelta
from random import randint
import sys
import os
import time
from abc import abstractmethod
import orjson
import dotenv
import argparse
import ssl

dotenv.load_dotenv()


def main_arguments() -> object:
    parser = argparse.ArgumentParser(description="Programme Meteo",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--type', '-t', dest='type', default='',
                        help="""Options: daily, today, interval""")
    parser.add_argument('--dates', '-d', dest='dates', default=[],
                        help="Date ou intervalle de dates. Ex: 2023-10-13 ou 2023-10-01,2023-10-13")
    parser.add_argument('--api-key', '-k', dest='key', default=0,
                        help="Numero de clé api pour la météo.")
    parser.add_argument('--env', '-v', dest='env', default="PROD",
                        help="Optionnel: environnement de l'api. PROD par défaut")
    return parser.parse_args()


ARGS_INFO = {
    '-t': {'long': '--type', 'dest': 'type', 'help': "Options: daily, today, interval"},
    '-d': {'long': '--dates', 'dest': 'dates', "help": "Date ou intervalle de dates. Ex: 2023-10-13 ou 2023-10-01,2023-10-13"},
    '-k': {'long': '--api-key', 'dest': 'key', 'help': "Numero de clé api pour la météo."},
    '-v': {'long': '--env', 'dest': 'env', 'help': "Optionnel: environnement de l'api. PROD par défaut"}
}


def check_arguments(args):
    miss = []
    if not getattr(args, ARGS_INFO['-t']['dest']):
        miss.append(
            f'-t ou {ARGS_INFO["-t"]["long"]} ({ARGS_INFO["-t"]["help"]})')
    elif args.type != 'today':
        if not getattr(args, ARGS_INFO['-d']['dest']):
            miss.append(
                f'-t ou {ARGS_INFO["-d"]["long"]} ({ARGS_INFO["-d"]["help"]})')

    return miss


# def clean():
#     files = ['locality_log.json', 'locality.csv', 'meteo_data.txt',
#              'meteo_log.json', 'meteo_url.json']
#     for file in files:
#         if os.path.exists(f'{os.environ.get("HISTORY_FOLDER")}/{file}'):
#             os.remove(file)


class MeteoAPI(object):

    def __init__(self, logfile: str, env: str) -> None:

        self.logfile = logfile
        self.nexties_api_key = os.environ.get(f"API_TOKEN_{env.upper()}")
        self.nexties_api_url = os.environ.get(f"API_URL_{env.upper()}")
        self.headers = {'Authorization': self.nexties_api_key,
                        'Content-Type': 'application/json'}
        self.history = {}
        self.http = None

    def get_request(self, url: str, header: bool = False) -> dict:
        try:
            response = None
            self.http = urllib3.PoolManager(cert_reqs='CERT_NONE')

            if header:
                print(url)
                response = self.http.request(
                    method='GET',
                    url=url,
                    headers=self.headers,
                    timeout=120
                )
            else:
                response = self.http.request(
                    method='GET',
                    url=url,
                    timeout=120
                )

            return orjson.loads(response.data)

        except urllib3.exceptions.HTTPError as e:
            print(e)
            print('==> Connexion failed!!')
            print(e.reason)
            sys.exit()

    def post_request(self, url: str, body: str) -> dict:
        self.attempt_post = 1
        self.http = urllib3.PoolManager(cert_reqs=ssl.CERT_NONE)
        try:
            response = self.http.request(
                method='POST',
                url=url,
                body=json.dumps(body),
                headers=self.headers
            )
            if response.status != 200:
                print("Post code: ", response.status)
            else:
                print("Upload successfully !!!")

        except urllib3.exceptions.HTTPError as e:
            print("Erreur post")
            print(e.reason)

    def set_log(self, log_key: str, value: object) -> None:
        logs = {}
        try:
            with open(f'{self.logfile}.json', 'r') as openfile:
                logs = json.load(openfile)
                logs[log_key] = value
        except FileNotFoundError:
            print('==> Log file not found')
            sys.exit()

        with open(f'{self.logfile}.json', 'w') as outfile:
            outfile.write(json.dumps(logs, indent=4))
        self.load_history()

    def get_log(self, log_key: str) -> object:
        try:
            self.load_history()
            return self.history[log_key]
        except Exception as e:
            print(f'errors : {e}')
            sys.exit()

    def load_history(self) -> None:
        try:
            with open(f'{self.logfile}.json', 'r') as openfile:
                self.history = json.load(openfile)
        except Exception as e:
            print(f'error: {e}')

    @abstractmethod
    def create_logfile(self) -> None:
        pass

    @abstractmethod
    def save(self):
        pass


class MeteoLocalityScraper(MeteoAPI):

    def __init__(self, logfile: str, file_output: str, env: str) -> None:
        super().__init__(logfile, env=env)
        self.file_output = file_output
        self.localities = []
        self.etab_loaded = False

    def create_logfile(self) -> None:
        log = {
            'total_page': 2,
            'last_page': 1,
        }
        if not os.path.exists(self.logfile):
            with open(f"{self.logfile}.json", "w") as logfile:
                logfile.write(json.dumps(log))

    def get_localities(self) -> None:
        print('==> loading all localities ...')
        has_next = True
        page = 1

        while has_next:
            result = self.get_request(
                f"{self.nexties_api_url}/localities?page={page}", header=True)

            if 'hydra:view' in result.keys() and 'hydra:next' in result['hydra:view']:
                has_next = True
            else:
                has_next = False

            for item in result['hydra:member']:
                if item['gps']:
                    location = item['gps'].split(',')
                    self.localities.append({
                        'id': item['id'],
                        'lat': location[0],
                        'long': location[1],
                        'name': item['name']
                    })

            page += 1

        self.save()

    def save(self) -> None:
        print('==> saving data ...')
        self.localities_file = f"{self.file_output}.csv"
        df = pd.DataFrame(self.localities)
        df.to_csv(self.localities_file, mode='w', header=True, index=False)
        self.localities.clear()

    def initialize(self):
        self.create_logfile()
        self.get_localities()
        print("==> All establishment loaded ('_')")


class MeteoAPIScraper(MeteoAPI):

    def __init__(self, logfile: str, data_source: str, url_file: str, output_file: str, env: str) -> None:
        super().__init__(logfile, env=env)
        self.data_source = data_source
        self.url_file = url_file
        self.output_file = output_file
        self.api_keys = os.environ.get("METEO_API_KEYS").split(',')
        self.urls = []
        self.dates = []
        self.meteo_key = 0

    def set_key_index(self, key):
        self.meteo_key = key

    def set_dates(self, dates):
        if len(dates) == 2:
            start_dt = datetime.strptime(dates[0], "%Y-%m-%d")
            end_dt = datetime.strptime(dates[1], "%Y-%m-%d")
            delta = timedelta(days=1)

            # store the dates between two dates in a list
            tmp = []

            while start_dt <= end_dt:
                # add current date to list by converting  it to iso format
                tmp.append(start_dt.strftime("%Y-%m-%d"))
                # increment start date by timedelta
                start_dt += delta

            self.dates = tmp

        else:
            self.dates = dates

    def get_missing_days(self):
        try:
            result = self.get_request(
                f"{self.nexties_api_url}/weathers/missing_days?dateFrom={self.dates[0]}&dateTo={self.dates[-1]}", header=True)

            if result and "dates" in result.keys():
                print("=> Jours manquants:")
                [print("-\t", day) for day in result['dates']]
        except Exception as e:
            print(e)

    def format_url(self, data: dict, date: str) -> str:
        api_key = self.api_keys[self.meteo_key]
        return {'locality_id': data['id'], 'url': f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{data['lat']}%2C{data['long']}/{date}/{date}/?unitGroup=us&key={api_key}&contentType=json"}

    def create_logfile(self) -> None:
        print('==> creating logfile !!')
        time.sleep(0.5)
        log = {'last_index': 0, 'total_index': 0, 'api_keys_usage': {}}
        if not os.path.exists(self.logfile):
            with open(f"{self.logfile}.json", "w") as logfile:
                logfile.write(json.dumps(log))

    def setup_config(self) -> None:
        print('==> configuring urls ...')
        time.sleep(.3)
        if os.path.exists(self.data_source):
            if not os.path.exists(f'{self.url_file}.json'):
                data = []
                data_source = pd.read_csv(self.data_source)

                counter = 0

                for x in range(len(data_source)):
                    for date in self.dates:
                        counter += 1
                        url = self.format_url(
                            data_source.loc[x].to_dict(), date)
                        data.append(url)

                        if counter == 45:
                            counter = 0
                            next_index = self.meteo_key + 1 if self.meteo_key + \
                                1 < len(self.api_keys) else 0
                            self.set_key_index(next_index)

                with open(f'{self.url_file}.json', 'w') as openfile:
                    openfile.write(json.dumps(data, indent=4))

                print('==> configuring url files done ...')
            else:
                print('==> url file already exist ...')

        else:
            print('==> data source not found ...')
        time.sleep(.5)

    def load_urls(self) -> None:
        print('==> Loading urls ...')
        time.sleep(.5)
        with open(f'{self.url_file}.json', 'r') as openfile:
            self.urls = json.loads(openfile.read())

    def extract(self, data: dict) -> dict:
        print('==> extracting data ...')
        response = data['days'][0]
        return {
            'locality': str(data['locality_id']),
            'dateWeather': response['datetime'],
            'timeWeather':  response['datetime'],
            'tempmax': response['tempmax'],
            'tempmin': response['tempmin'],
            'temp': response['temp'],
            'dew': response['dew'],
            'humidity': response['humidity'],
            'snow': response['snow'],
            'windspeed': response['windspeed'],
            'cloudcover': response['cloudcover'],
            'sunrise': f"{response['datetime']} {response['sunrise']}",
            'sunset': f"{response['datetime']} {response['sunset']}",
            'conditions': response['conditions'],
            'description': response['description']
        }

    def save(self, data: dict):
        print('==> saving data ...')

        result = f"\n{data['locality']}${data['dateWeather']}${data['timeWeather']}${data['tempmax']}${data['tempmin']}${data['temp']}${data['dew']}${data['humidity']}${data['snow']}${data['windspeed']}${data['cloudcover']}${data['sunrise']}${data['sunset']}${data['conditions']}${data['description']}#"
        with open(f'{self.output_file}.txt', 'a') as filesave:
            filesave.write(result)

    def upload(self):

        text = ""

        with open(f'{self.output_file}.txt', 'r') as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                if len(row):
                    text += ''.join(row)

        self.post_request(
            f"{self.nexties_api_url}/weatthers/upload", {'data_content': text})

    def start(self):
        self.create_logfile()
        self.setup_config()
        self.load_urls()
        self.load_history()
        total = len(self.urls)

        for x in range(total):
            print(
                f"==> locality {x+1} / {total}")
            req_data = self.get_request(self.urls[x]['url'])
            req_data['locality_id'] = self.urls[x]['locality_id']
            clean_data = self.extract(req_data)
            self.save(clean_data)
            time.sleep(.5)


if __name__ == '__main__':

    history_filename = f'{os.environ.get("HISTORY_FOLDER")}/meteo/meteo-scraping-log.txt'

    now = datetime.now()
    if os.path.exists(history_filename):
        with open(history_filename, 'a', encoding='utf-8') as file:
            file.write("Démarrage scrap meteo: " +
                       now.strftime("%d/%m/%Y %H:%M:%S"))
    else:
        with open(history_filename, 'w', encoding='utf-8') as file:
            file.write("Démarrage scrap meteo: " +
                       now.strftime("%d/%m/%Y %H:%M:%S"))

    args = main_arguments()

    miss = check_arguments(args)

    if not len(miss):

        try:

            datetime_now = datetime.now().strftime("%Y-%m-%d %H_%M")
            d = MeteoLocalityScraper(
                f'{os.environ.get("HISTORY_FOLDER")}/meteo/locality_log_{datetime_now}', f'{os.environ.get("HISTORY_FOLDER")}/locality_{datetime_now}', env=args.env)
            d.initialize()
            time.sleep(2)
            m = MeteoAPIScraper(f'{os.environ.get("HISTORY_FOLDER")}/meteo/locality_log_{datetime_now}', d.localities_file,
                                f'{os.environ.get("HISTORY_FOLDER")}/meteo/meteo_url_{datetime_now}', f'{os.environ.get("HISTORY_FOLDER")}/meteo_data_{datetime_now}', env=args.env)
            if args.dates:
                m.set_dates(args.dates.split(','))
            else:
                m.set_dates([datetime.now().strftime('%Y-%m-%d')])

            m.set_key_index(int(args.key))
            if args.type == "missing-days":
                m.get_missing_days()
            else:
                m.start()
                m.upload()

        except Exception as e:
            now = datetime.now()
            with open(history_filename, 'a', encoding='utf-8') as file:
                file.write("  ===>  Fin scrap meteo WITH ERRORS: " +
                           now.strftime("%d/%m/%Y %H:%M:%S") + ':' + str(e) + '\n')

        now = datetime.now()

        with open(history_filename, 'a', encoding='utf-8') as file:
            file.write("  ===>  Fin scrap meteo: " +
                       now.strftime("%d/%m/%Y %H:%M:%S") + '\n')

    else:
        now = datetime.now()
        with open(history_filename, 'a', encoding='utf-8') as file:
            file.write("  ===>  Fin scrap meteo WITH ERRORS: " +
                       now.strftime("%d/%m/%Y %H:%M:%S") + ':' + f"Argument(s) manquant(s): {', '.join(miss)}" + '\n')
