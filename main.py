from dividend_safety.finanzen_net import DividendSafetyReport

r = DividendSafetyReport()
df = r.assemble_companies(['3m',
                           'abbvie', 'amgen', 'apple', 'astellas_pharma', 'bayer', 'cisco', 'corning', 'diageo',
                           'deere', 'disney', 'ecolab', 'fuchs_petrolub_vz', 'gilead_sciences', 'hasbro', 'henkel_vz',
                           'inditex', 'intel', 'international_flavorsfragrances', 'johnsonjohnson', 'kao', 'kddi',
                           'kion', 'kla-tencor', 'mccormick', 'mcdonalds', 'microsoft', 'nike', 'pepsico',
                           'procter_gamble', 'rational', 'reckitt_benckiser', 'siemens_healthineers', 'ao_smith',
                           'spirax-sarco_engineering_4', 'starbucks', 'texas_instruments', 'unilever', 'vf',
                           'waste_management', 'wpp_2012', 'xp_power',
                           'xylem'])
df.to_excel(r'C:\Users\berun\Desktop\dividend_safety_report.xlsx', index=False)
