import json
from os import path, environ
import dotenv
from datetime import datetime
import re

dotenv.load_dotenv()


class Scraping(object):
    def __init__(self, items: list) -> None:
        self.posts = []
        self.page_data = {}
        self.items = items
        self.establishment = ''
        self.url = ''
        self.current_credential = {}
        self.name = ''
        self.hashtag = ''
        self.env = "DEV"

    def set_environ(self, env):
        self.env = env

    def set_current_credential(self, index):
        self.current_credential = self.credentials[index]

    def set_credentials(self, source: str) -> None:
        logins_path = path.join(path.dirname(__file__), 'logins.json')
        with open(logins_path, 'r') as f:
            data = json.load(f)
            self.credentials = data[source]

        if len(self.credentials):
            self.set_current_credential(0)

    def set_item(self, item):
        self.establishment = item['establishment_id']
        self.url = item['url']
        self.name = item['establishment_name']

    def save(self):

        try:
            page_data = self.page_data
            page_data['posts'] = self.posts
            page_data['url'] = self.url
            page_data['createdAt'] = datetime.now().strftime('%Y-%m-%d')
            page_data['hasStat'] = "0"

            try:
                e_name = re.sub(r'[^a-zA-Z0-9\s]+', '',
                                self.name).replace(' ', '_')

                output_file = f"{self.env}_hashtag_{page_data['source']}_{self.hashtag}_{self.establishment}_{e_name}_{datetime.now().strftime('%Y-%m-%d')}"
            except Exception as e:
                print(e)

            print(output_file)

            with open(f"{environ.get('SOCIAL_FOLDER')}/{output_file}.json", 'w') as foutput:
                json.dump(page_data, foutput, indent=4, sort_keys=True)

            self.posts = []
            self.page_data = {}

            return output_file
        except Exception as e:
            print(e)

    def stop(self):
        pass
