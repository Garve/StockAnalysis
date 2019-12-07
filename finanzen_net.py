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

    @staticmethod
    def number_string_to_float(number, percentage=True):
        number = number.replace(',', '.')
        if percentage:
            return float(number[:-1]) / 100
        else:
            return float(number)

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
                            dividends.append(self.number_string_to_float(dividend.strip(), percentage=False))

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

    def get_years_of_increase(self):
        if self.dividend_table is None:
            self.get_dividends()
        s = self.dividend_table.diff()
        now = s.index[0]
        decrease = s[s > 0].index.max()
        if decrease is not pd.np.nan:
            return now - decrease - 1
        else:
            return len(self.dividend_table)

    def get_dividend_coverage(self):
        res = namedtuple('DividendCoverage', 'earnings_growth dividend_yield payout_ratio')

        table = self.fundamentals_soup.find_all('div', class_='table-responsive')[-2]
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if tds[0].get_text() == 'langfristiges Wachstum':
                res.earnings_growth = self.number_string_to_float(tds[1].get_text())
            elif tds[0].get_text() == 'Dividenden Rendite':
                res.dividend_yield = self.number_string_to_float(tds[1].get_text())
                res.payout_ratio = self.number_string_to_float(re.findall(' ([0-9,]+)%', tds[4].get_text())[0])
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
