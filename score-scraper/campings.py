from scraping import Scraping
import time


class Campings(Scraping):
    def __init__(self, url: str, establishment: str,establishment_name: str, env: str):
        defurl = url if url.endswith('.fr.html') else f"{url}.fr.html"
        super().__init__(in_background=False, url=defurl,
                         establishment=establishment, establishment_name=establishment_name, env=env)

        self.attr = 'class'
        self.balise = 'span'
        self.css_selector = 'summary__value'
        self.source = 'campings'


# trp = Campings(
#     url="https://www.campings.com/fr/camping/le-pearl-camping-paradis-76750#reviews", establishment=4, env="DEV")
# trp.execute()
# print(trp.data)
