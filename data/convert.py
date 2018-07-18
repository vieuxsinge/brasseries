import csv
import json

csvfile = open('population.csv', 'r')
jsonfile = open('population.json', 'w')

fieldnames = ("departement","nom","population","not", "so", "useful")
reader = csv.DictReader( csvfile, fieldnames)
rows = {}
for row in reader:
    rows[row['departement']] = row['population']
json.dump(rows, jsonfile)
