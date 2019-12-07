from finanzen_net import FinanzenNet, Dividend, Moodys

finanzen_net = FinanzenNet('bayer')
dividend = Dividend(finanzen_net)
moodys = Moodys(finanzen_net)

try:
    print('Outlook:', moodys.get_outlook())
except LookupError as error:
    print(error)

try:
    print('Credit rating:', moodys.get_credit_rating())
except LookupError as error:
    print(error)

try:
    print('Risk score:', moodys.get_risk_score())
except LookupError as error:
    print(error)

print('Dividend history:')
print(dividend.get_dividends())

n_years = 5
print(f'Average annual dividend growth rate in the last {n_years} years:')
print(dividend.get_growth_rate(n_years))

dividend_coverage = dividend.get_dividend_coverage()
print(f'Dividend yield is {dividend_coverage.dividend_yield:.2%}. {dividend_coverage.payout_ratio:.2%} of the earnings are needed for covering this. The earning will grow by {dividend_coverage.earnings_growth:.2%} each year until 2021')