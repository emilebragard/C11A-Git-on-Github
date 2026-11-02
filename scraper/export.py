"""Write the clean deliverable data/coaches.csv from the working file
data/coaches_full.csv: drops internal columns (url, status, phone)."""
import csv
DROP = {'url', 'status', 'phone'}
rows = list(csv.DictReader(open('data/coaches_full.csv')))
F = [f for f in rows[0] if f not in DROP]
w = csv.DictWriter(open('data/coaches.csv', 'w'), fieldnames=F, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
print('exported', len(rows), 'rows, columns:', F)
