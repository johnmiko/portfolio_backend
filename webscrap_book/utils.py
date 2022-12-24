from enum import Enum

from selenium.webdriver.support.wait import WebDriverWait


class Book:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.name_underscore = name.replace(' ', '_')
        self.name_dash = name.replace(' ', '-')


class Website:
    def __init__(self, base_url):
        self.base_url = base_url

    def create_url(self, book, page_number, total_pages):
        return f'{self.base_url}{book.number}/page-{page_number}-{book.name_dash}/{page_number}/{total_pages}'

    def get_text(self, driver):
        all_text_els = WebDriverWait(driver, 1).until(lambda driver:
                                                      driver.find_elements('xpath',
                                                                           "//p[@class='storyText story-text']"))
        all_text = [text_el.text for text_el in all_text_els]
        all_text2 = '\n'.join(all_text)
        all_text2 = all_text2.encode('latin1', 'ignore').decode("latin1")
        return all_text2


class Websites(Enum):
    all_free_novel = 'https://www.allfreenovel.com/Page/Story/'


class WebsiteFactory:
    @staticmethod
    def create(name):
        if name == Websites.all_free_novel:
            return Website(Websites.all_free_novel.value)
