from scrapy import Spider, FormRequest, Request
from scrapy.selector import Selector
from bs4 import BeautifulSoup
import re
import json
from digi_scrape.items import DigiOrder


BASE_URL = "https://www.digikala.com"
USER_NAME = input("Enter your digikala account username: ")
PASSWORD = input("Enter your digikala account password: ")
JSON_OUTPUT = "temp.json"


class DigiBoughtSpider(Spider):
    name = "digi_bought_scrape"
    start_urls = [BASE_URL+'/profile/orders/']

    def parse(self, response):
        yield FormRequest(BASE_URL+"/users/login/", formdata={'login[email_phone]': USER_NAME, 'login[password]': PASSWORD, 'login[remember]': "1"}, callback=self.action)

    def close(self, reason):
        with open(JSON_OUTPUT, 'r') as f:
            obj = json.loads(f.read())
        sum = 0
        for item in obj:
            sum += item['price']

        print("\n\nTotal money spent in digikala: %d Tomans\n\n" % sum)

    def action(self, response):
        if '/profile/orders/' not in response.request.url:
            yield Request(
                response.urljoin(BASE_URL+'/profile/orders/'),
                callback=self.action
            )
            return
        page_soup = BeautifulSoup(response.text, 'html.parser')
        orders = page_soup.findAll(
            'div', attrs={'class': "c-table-orders__row"})
        del orders[0]

        for order in orders:
            if len(re.findall(r"payment-status--ok", str(order))) == 0:
                continue
            digi_order = DigiOrder()
            digi_order['hash_'] = re.search(
                r"hash\">\s*(\d*)\n", str(order)).group(1)
            digi_order['hash_'] = int(digi_order['hash_'])
            digi_order['date'] = order.find(
                'div', class_="c-table-orders__cell c-table-orders__cell--date").text
            digi_order['price'] = 0
            for piece in re.search(r"--price\">\s*(\S+)\s*تومان", str(order)).group(1).split(','):
                digi_order['price'] = digi_order['price']*1000 + int(piece)
            yield(digi_order)

        pager = page_soup.find('div', attrs={'class':"c-pager"})
        next_page = re.search(r'is-active".*?href.*?href="(.+?)"', str(pager))
        if next_page:
            next_page = next_page.group(1)
            yield Request(
                response.urljoin(BASE_URL+next_page),
                callback=self.action
            )
