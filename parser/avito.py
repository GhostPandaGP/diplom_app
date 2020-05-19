import logging
from collections import namedtuple
import datetime
from time import sleep
from math import ceil
import random

import requests
import bs4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('avito')

InnerBlock = namedtuple(
    'Block',
    'text,url'
)


class Block(InnerBlock):

    def __str__(self):
        return f'{self.title}\t{self.price} {self.currency}\t{self.date}\t{self.url}'


class AvitoParser:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User - Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0',
            'Accept - Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        }

    def get_pagination_limit(self, url: str):
        text = self.get_page(url=url)
        print(text)
        soup = bs4.BeautifulSoup(text, 'lxml')

        block = soup.select_one('span.page-title-count-1oJOc')
        limit = int(block.get_text()) / 51
        limit = ceil(limit)

        logger.debug(f"Число страниц будет: {limit}")

        return limit

    def get_page(self, url: str, page: int = None):
        params = {
            'radius': 0,
            'user': 1
        }  # это параметры get запроса
        if page and page > 1:
            params['p'] = page

        # url = 'https://www.avito.ru/sankt-peterburg/avtomobili/bmw/5'
        # url = 'https://www.avito.ru/sankt-peterburg/avtomobili/citroen/c4'
        # url = 'https://www.avito.ru/sankt-peterburg/avtomobili/citroen/c3_picasso'
        url = 'https://www.avito.ru' + url
        r = self.session.get(url, params=params)
        return r.text

    @staticmethod
    def parse_block(url: str, text: str):
        soup = bs4.BeautifulSoup(text, 'lxml')
        item = soup.select('div.item-view-block div.item-description div.item-description-text')
        if len(item) < 1:
            return "Error in parse item and get text"
        item = item[0].get_text('\n')

        result_text = item.replace('<p>', '').replace('</p>', '').replace('<strong>', '').replace('</strong>', '')

        url = 'https://www.avito.ru' + url
        logger.info(f'%s, %s', url, result_text)

        return Block(
            url=url,
            text=result_text
        )

    def get_links(self, url: str, page: int = None):
        text = self.get_page(page=page, url=url)
        soup = bs4.BeautifulSoup(text, 'lxml')

        # Запрашиваем ссылки, по которым будем итерироваться
        links = soup.select(
            'div.item__line a.snippet-link'
        )
        print(len(links))
        for link in links:
            link = link.get('href')
            logger.info(link)
            text_card = self.get_page(url=link)
            block = self.parse_block(url=link, text=text_card)
            logger.info(block)
            sleep(1 + random.randint(0, 10) / 10)

    def parse_all(self):
        base_url = '/rossiya?q=оберег'
        limit = self.get_pagination_limit(url=base_url)
        # print(limit)
        logger.info(f'Всего страниц: {limit}')
        limit = 1

        for i in range(1, limit + 1):
            self.get_links(page=i, url=base_url)
            sleep(1 + random.randint(0, 10) / 10)


def main():
    p = AvitoParser()
    p.parse_all()
    # p.get_pagination_limit()


if __name__ == "__main__":
    main()
