from db import properties_col
import csv

docs = list(properties_col.find({}))

keys = set()
rows = []

for d in docs:
    row = {}
    for k, v in d.items():
        row[k] = str(v)
        keys.add(k)
    rows.append(row)

keys = list(keys)

with open("properties_export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=keys)
    writer.writeheader()
    writer.writerows(rows)

print("Exported", len(rows), "rows to properties_export.csv")
