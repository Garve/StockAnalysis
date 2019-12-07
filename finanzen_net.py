from collections import namedtuple

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re


class FinanzenNet:
    def __init__(self, company):
        self.company = company
        self.dividend_soup = self.get_dividend_page()
        self.stock_soup = self.get_stock_page()
        self.fundamentals_soup = self.get_fundamentals_page()

    def get_dividend_page(self):
        page = requests.get(f'https://www.finanzen.net/dividende/{self.company}')
        return BeautifulSoup(page.content, 'html.parser')

    def get_stock_page(self):
        page = requests.get(f'https://www.finanzen.net/aktien/{self.company}')
        return BeautifulSoup(page.content, 'html.parser')

    def get_fundamentals_page(self):
        page = requests.get(f'https://www.finanzen.net/fundamentalanalyse/{self.company}')
        return BeautifulSoup(page.content, 'html.parser')


class Dividend:
    def __init__(self, finanzen_net):
        self.dividend_table = None
        self.company = finanzen_net.company
        self.dividend_soup = finanzen_net.dividend_soup
        self.fundamentals_soup = finanzen_net.fundamentals_soup

    def get_dividends(self, force=False):
        if force or self.dividend_table is None:
            dividends = []
            years = []

            for dividend_information in self.dividend_soup.find_all('div', class_='table-responsive')[-2:]:
                for tr in dividend_information.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) > 4:
                        dividend = tds[2].get_text()
                        year = tds[4].get_text()
                        if not dividend.startswith('*'):
                            years.append(int(year))
                            dividends.append(float(dividend.strip().replace(',', '.')))

            self.dividend_table = pd.Series(data=dividends, index=years)
            return self.dividend_table

    def get_growth_rate(self, n_years=5):
        if self.dividend_table is None:
            self.get_dividends()
        if len(self.dividend_table) > n_years:
            if self.dividend_table.values[n_years] != 0:
                return (self.dividend_table.values[0] / self.dividend_table.values[n_years]) ** (1 / n_years) - 1
            else:
                raise ZeroDivisionError(f'Dividend of {self.company} {n_years} years ago was zero.')
        else:
            raise IndexError(f'No dividend history for {self.company} {n_years} years ago.')

    def get_dividend_coverage(self):
        res = namedtuple('DividendCoverage', 'earnings_growth dividend_yield payout_ratio')

        table = self.fundamentals_soup.find_all('div', class_='table-responsive')[-2]
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if tds[0].get_text() == 'langfristiges Wachstum':
                res.earnings_growth = float(tds[1].get_text()[1:-1].replace(',', '.')) / 100
            elif tds[0].get_text() == 'Dividenden Rendite':
                res.dividend_yield = float(tds[1].get_text()[1:-1].replace(',', '.')) / 100
                res.payout_ratio = float(re.findall(' ([0-9,]+)\%', tds[4].get_text())[0].replace(',', '.')) / 100
        return res


class Moodys:
    def __init__(self, finanzen_net):
        self.company = finanzen_net.company
        self.stock_soup = finanzen_net.stock_soup

    def get_credit_rating(self):
        potential_credit_score = self.stock_soup.find('div', class_="tachoValue tachoMr mr4")
        if potential_credit_score:
            return potential_credit_score.get_text()
        else:
            raise LookupError(f'No credit score for {self.company}.')

    def get_risk_score(self):
        potential_credit_score = self.stock_soup.find('div', class_="tachoValue tachoMcrs mr1")
        if potential_credit_score:
            return potential_credit_score.get_text()
        else:
            raise LookupError(f'No risk score for {self.company}.')

    def get_outlook(self):
        potential_outlook = self.stock_soup.find('div', class_='tachoValue tachoKz')
        if potential_outlook:
            return float(potential_outlook.find('strong').get_text()[1:-1].replace(',', '.')) / 100
        else:
            raise LookupError(f'No outlook for {self.company}.')
