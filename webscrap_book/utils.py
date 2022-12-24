from abc import ABC, abstractmethod
from enum import Enum

from selenium.webdriver.support.wait import WebDriverWait


class Websites(Enum):
    all_free_novel = 'https://www.allfreenovel.com/Page/Story/'
    gemibook = 'https://gemibook.com/'


class WebsiteFactory:
    @staticmethod
    def create(name):
        if name == Websites.all_free_novel:
            return AllFreeNovelWebsite()
        elif name == Websites.gemibook:
            return GemiBookWebsite()
        # https://gemibook.com/project-hail-mary/p-1-10077539


class Book:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.name_underscore = name.replace(' ', '_')
        self.name_dash = name.replace(' ', '-')


class Website(ABC):
    @abstractmethod
    def create_url(self, book, page_number, total_pages):
        raise NotImplementedError()

    @abstractmethod
    def get_text(self, driver):
        raise NotImplementedError()


class AllFreeNovelWebsite(Website):
    base_url = Websites.all_free_novel.value

    def create_url(self, book, page_number, total_pages):
        return f'{self.base_url}{book.number}/page-{page_number}-{book.name_dash}/{page_number}/{total_pages}'

    def get_text(self, driver):
        text_els = WebDriverWait(driver, 1).until(lambda driver:
                                                  driver.find_elements('xpath',
                                                                       "//p[@class='storyText story-text']"))
        text_list = [text_el.text for text_el in text_els]
        text = '\n'.join(text_list)
        text2 = text.encode('latin1', 'ignore').decode("latin1")
        return text2


class GemiBookWebsite(Website):
    base_url = Websites.gemibook.value

    def create_url(self, book, page_number, total_pages):
        # https://gemibook.com/project-hail-mary/p-1-10077539
        # https://gemibook.com//Project-Hail-Mary/p-1-10077539
        return f'{self.base_url}{book.name_dash.lower()}/p-{page_number}-{int(book.number) + int(page_number) - 1}'

    def get_text(self, driver):
        text_elements = WebDriverWait(driver, 1).until(lambda driver:
                                                       driver.find_elements('xpath',
                                                                            "//div[@class='chapter-content']"))
        text_list = [text_el.text for text_el in text_elements]
        text = '\n'.join(text_list)
        text2 = text.encode('latin1', 'ignore').decode("latin1")
        return text2
