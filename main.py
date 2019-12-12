from finanzen_net import DividendSafetyReport

r = DividendSafetyReport()
df = r.assemble_companies(['pepsico', '3m', 'bayer'])
print()