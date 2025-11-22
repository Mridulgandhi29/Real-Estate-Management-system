# app.py
from db import properties_col, owners_col, transactions_col, client
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, UTC
import json
import csv
from pymongo.errors import OperationFailure
import re

def insert_property():
    ti = input("title: ").strip()
    city = input("city: ").strip()
    if not title or not city:
        print("Title and city are required.")
        return
    try:
        price = int(input("price: "))
        if price < 0:
            print("Price cannot be negative.")
            return
    except ValueError:
        print("Price must be a number.")
        return
    doc = {"title": title, "city": city, "price": price, "status": "available", "created_at": datetime.now(UTC)}
    res = properties_col.insert_one(doc)
    print("Inserted id:", res.inserted_id)

def list_properties(page=1, per_page=5):
    skip = (page-1)*per_page
    docs = list(properties_col.find({}).sort("price", 1).skip(skip).limit(per_page))
    if not docs:
        print("No properties found.")
        return
    for d in docs:
        print(json.dumps(d, default=str, indent=2))

def find_by_city():
    city = input("city: ").strip()
    if not city:
        print("City cannot be empty.")
        return
    # Case-insensitive partial match
    pattern = re.escape(city)
    docs = list(properties_col.find({"city": {"$regex": pattern, "$options": "i"}}))
    if not docs:
        print("No properties in", city)
        return
    for d in docs:
        print(json.dumps(d, default=str, indent=2))

def update_price():
    pid = input("property id: ").strip()
    try:
        newp = int(input("new price: "))
        if newp < 0:
            print("Price cannot be negative.")
            return
    except ValueError:
        print("Price must be a number.")
        return
    try:
        obj_id = ObjectId(pid)
    except InvalidId:
        print("Invalid property id format.")
        return
    try:
        r = properties_col.update_one({"_id": obj_id}, {"$set": {"price": newp}})
        print("Modified count:", r.modified_count)
    except Exception as e:
        print("Error updating:", e)

def delete_property():
    pid = input("property id: ").strip()
    try:
        obj_id = ObjectId(pid)
    except InvalidId:
        print("Invalid property id format.")
        return
    try:
        r = properties_col.delete_one({"_id": obj_id})
        print("Deleted count:", r.deleted_count)
    except Exception as e:
        print("Error deleting:", e)

def create_index():
    i1 = properties_col.create_index([("city", 1)])
    i2 = properties_col.create_index([("price", 1)])
    print("Created indexes:", i1, i2)
    print("Indexes:", properties_col.index_information())

def avg_price_per_city():
    pipeline = [{"$group": {"_id": "$city", "avgPrice": {"$avg": "$price"}, "count": {"$sum": 1}}}]
    res = list(properties_col.aggregate(pipeline))
    if not res:
        print("No aggregate results.")
        return
    for r in res:
        print(r)

def export_csv():
    docs = list(properties_col.find({}))
    if not docs:
        print("No documents to export.")
        return
    # Gather all field names
    fieldnames = set()
    rows = []
    for d in docs:
        row = {}
        for k, v in d.items():
            if k == "_id":
                row[k] = str(v)
            else:
                row[k] = v
            fieldnames.add(k)
        rows.append(row)
    fieldnames = list(fieldnames)
    path = "properties_export.csv"
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print("Exported to", path)
    except Exception as e:
        print("Failed to export:", e)

def purchase_transaction():
    print("NOTE: Transactions require a replica set or Atlas. If you're running local MongoDB without a replica set this may fail.")
    pid = input("property id: ").strip()
    buyer = input("buyer name: ").strip()
    if not buyer:
        print("Buyer name is required.")
        return
    try:
        price = int(input("offer price: "))
        if price < 0:
            print("Offer price cannot be negative.")
            return
    except ValueError:
        print("Offer price must be a number.")
        return

    try:
        obj_id = ObjectId(pid)
    except InvalidId:
        print("Invalid property id format.")
        return

    try:
        # First attempt transactional flow
        try:
            with client.start_session() as session:
                with session.start_transaction():
                    r = properties_col.update_one({"_id": obj_id, "status": "available"}, {"$set": {"status": "sold"}}, session=session)
                    if r.modified_count == 0:
                        raise Exception("Not available")
                    transactions_col.insert_one({"property_id": obj_id, "buyer_name": buyer, "price": price, "date": datetime.now(UTC)}, session=session)
            print("Purchase success (transaction)")
            return
        except OperationFailure:
            # server doesn't support transactions, fall back
            pass

        # Non-transactional fallback
        r = properties_col.update_one({"_id": obj_id, "status": "available"}, {"$set": {"status": "sold"}})
        if r.modified_count == 0:
            print("Not available")
            return
        try:
            transactions_col.insert_one({"property_id": obj_id, "buyer_name": buyer, "price": price, "date": datetime.now(UTC)})
            print("Purchase success (no transactions available on this server)")
        except Exception as ie:
            print("Property marked sold but failed to record transaction:", ie)
    except Exception as e:
        print("Transaction failed:", e)

MENU = """
1) Insert property
2) List properties (page)
3) Find by city
4) Update price
5) Delete property
6) Create indexes
7) Avg price per city (aggregate)
8) Export CSV (backup)
9) Purchase (transaction demo)
0) Exit
"""

def main():
    while True:
        print(MENU)
        c = input("Choose: ").strip()
        if c == "1":
            insert_property()
        elif c == "2":
            try:
                p = int(input("page (1): ") or 1)
            except ValueError:
                p = 1
            list_properties(page=p)
        elif c == "3":
            find_by_city()
        elif c == "4":
            update_price()
        elif c == "5":
            delete_property()
        elif c == "6":
            create_index()
        elif c == "7":
            avg_price_per_city()
        elif c == "8":
            export_csv()
        elif c == "9":
            purchase_transaction()
        elif c == "0":
            break
        else:
            print("Invalid")

if __name__ == "__main__":
    main()
