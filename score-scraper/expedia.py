from scraping import Scraping
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time


class Expedia(Scraping):
    def __init__(self, url: str, establishment: str, establishment_name: str, env: str):
        super().__init__(in_background=True, url=url,
                         establishment=establishment, establishment_name=establishment_name, env=env)

        self.xpath_selector = None
        self.xpath_selector_2 = None

        if self.url.endswith("Description-Hotel"):
            self.xpath_selector = "//meta[@itemprop='ratingValue']"

        if self.url.endswith("Avis-Voyageurs"):
            self.xpath_selector_2 = "//section[@id='Reviews']/div/div/div/div/div/div/span/div/div/div/span/div"

        self.source = 'expedia'

    def extract(self) -> None:
        time.sleep(2)

        try:
            if self.xpath_selector:
                element = self.driver.find_element(By.XPATH, self.xpath_selector)
                score_content = element.get_attribute('content')
                if score_content:
                    score = float(score_content.replace(',', '.'))

            elif self.xpath_selector_2:
                element = self.driver.find_element(By.XPATH, self.xpath_selector_2)
                score_text = element.text.strip()
                if score_text:
                    score = float(score_text.replace(',', '.'))

        except NoSuchElementException:
            print("Élément non trouvé pour les sélecteurs XPath fournis.")
        except TimeoutException:
            print("Temps d'attente dépassé pour trouver l'élément.")
        except Exception as e:
            print(f"Erreur inattendue: {e}")

        self.data = score / 2


# Exemple d'utilisation
# trp = Expedia(url="https://www.expedia.com/Les-Deserts-Hotels-Vacanceole-Les-Balcons-DAix.h2481279.Hotel-Reviews",
#               establishment="4", env="DEV")
# trp.execute()
# print(trp.data)
