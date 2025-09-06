import csv
import os

def find_ticket_by_hash(hashed_token, csv_file="tickets.csv"):
    if not os.path.exists(csv_file):
        return None
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            if row.get('hashed_token') == hashed_token:
                return row
    return None