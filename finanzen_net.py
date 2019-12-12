from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import shelve


class FinanzenNet:
    def __init__(self, company, force_reload=False):
        self.company = company

        self.dividend_soup = self.get_page('dividende', force_reload)
        self.stock_soup = self.get_page('aktien', force_reload)
        self.fundamentals_soup = self.get_page('fundamentalanalyse', force_reload)

    def get_page(self, website_category, force_reload):
        with shelve.open('finanzen_net.shelve') as s:
            saving_name = '/'.join([self.company, website_category])
            if saving_name in s.keys() and not force_reload:
                print(f'Loading {self.company}/{website_category} from disk...')
                page = s[saving_name]
            else:
                print(f'Downloading {self.company}/{website_category} from finanzen.net...')
                page = requests.get(f'https://www.finanzen.net/{website_category}/{self.company}')
                s[saving_name] = page
        return BeautifulSoup(page.content, 'html.parser')


class DividendData:
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
                    try:
                        dividend = tds[2].get_text()
                        year = tds[4].get_text()
                        try:
                            year = int(year)
                            dividend = self.number_string_to_float(dividend.strip(), percentage=False)
                        except ValueError:
                            continue

                        dividends.append(dividend)
                        years.append(year)
                    except IndexError:
                        continue

            self.dividend_table = pd.Series(data=dividends, index=years)
            return self.dividend_table

    def get_growth_rate(self, n_years=5):
        if self.dividend_table is None:
            self.get_dividends()
        try:
            return (self.dividend_table.values[0] / self.dividend_table.values[n_years]) ** (1 / n_years) - 1
        except (ZeroDivisionError, IndexError):
            return pd.np.nan

    def get_years_of_increase(self):
        if self.dividend_table is None:
            self.get_dividends()
        tmp = self.dividend_table.tolist()
        try:
            i = 0
            while tmp[i] >= tmp[i + 1]:
                i += 1
            return i
        except IndexError:
            return len(tmp) if tmp else pd.np.nan

    def get_dividend_coverage(self):
        res = namedtuple('DividendCoverage', 'earnings_growth forward_dividend_yield forward_payout_ratio')

        table = self.fundamentals_soup.find_all('div', class_='table-responsive')[-2]
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if tds[0].get_text() == 'langfristiges Wachstum':
                try:
                    res.earnings_growth = self.number_string_to_float(tds[1].get_text())
                except ValueError:
                    res.earnings_growth = pd.np.nan
            elif tds[0].get_text() == 'Dividenden Rendite':
                try:
                    res.forward_dividend_yield = self.number_string_to_float(tds[1].get_text())
                except ValueError:
                    res.forward_dividend_yield = pd.np.nan

                try:
                    res.forward_payout_ratio = self.number_string_to_float(
                        re.findall(' ([0-9,]+)%', tds[4].get_text())[0])
                except (ValueError, IndexError):
                    res.forward_payout_ratio = pd.np.nan
        return res


class Moodys:
    def __init__(self, finanzen_net):
        self.company = finanzen_net.company
        self.stock_soup = finanzen_net.stock_soup

    def get_credit_rating(self):
        try:
            return self.stock_soup.find('div', class_="tachoValue tachoMr mr4").get_text()
        except AttributeError:
            return pd.np.nan

    def get_risk_score(self):
        try:
            return self.stock_soup.find('div', class_="tachoValue tachoMcrs mr1").get_text()
        except AttributeError:
            return pd.np.nan


class DividendSafetyReport:
    def _assemble_single_company(self, company):
        finanzen_net = FinanzenNet(company)
        dividend = DividendData(finanzen_net)
        moodys = Moodys(finanzen_net)

        dividend_growth_rate = dividend.get_growth_rate()
        dividend_increasing_years = dividend.get_years_of_increase()

        coverage = dividend.get_dividend_coverage()
        dividend_yield = coverage.forward_dividend_yield
        earnings_growth = coverage.earnings_growth
        payout_ratio = coverage.forward_payout_ratio

        credit_rating = moodys.get_credit_rating()
        risk_score = moodys.get_risk_score()

        return pd.DataFrame(
            [(company, dividend_growth_rate, dividend_increasing_years, dividend_yield, earnings_growth, payout_ratio,
              credit_rating, risk_score)],
            columns=['Name', 'Dividend Growth', 'Dividend Increase', 'Dividend Yield', 'Earning Growth', 'Payout Ratio',
                     'Credit Rating', 'Risk Score']
        )

    def assemble_companies(self, companies):
        with ThreadPoolExecutor(max_workers=4) as executor:
            res = executor.map(self._assemble_single_company, companies)
        return pd.concat(res)
