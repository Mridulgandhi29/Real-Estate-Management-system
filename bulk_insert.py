# bulk_insert.py
from db import properties_col
from datetime import datetime, UTC

properties = [
    ("Ocean View Apartment", "Mumbai", 4500000),
    ("Skyline Residency", "Mumbai", 5200000),
    ("Blue Orchid Flat", "Mumbai", 6100000),
    ("Sunshine Towers", "Mumbai", 7000000),
    ("Hillcrest Home", "Mumbai", 4300000),

    ("Royal Residency", "Delhi", 3900000),
    ("Green Valley Apartment", "Delhi", 4700000),
    ("Pearl Heights", "Delhi", 5600000),
    ("Urban Nest", "Delhi", 5100000),
    ("Maple Homes", "Delhi", 6000000),

    ("Blossom Apartment", "Pune", 3200000),
    ("Crystal Court", "Pune", 3500000),
    ("Riverfront Flats", "Pune", 4000000),
    ("Silver Oak Homes", "Pune", 3700000),
    ("GreenStone Residency", "Pune", 4500000),

    ("Tech Hub Apartment", "Bangalore", 5500000),
    ("Lakeside Homes", "Bangalore", 6300000),
    ("Metro View Flats", "Bangalore", 5900000),
    ("Elite Enclave", "Bangalore", 7000000),
    ("Harmony Residency", "Bangalore", 4800000),

    ("Seawind Apartment", "Chennai", 4100000),
    ("Coral Homes", "Chennai", 5200000),
    ("Marina Residency", "Chennai", 4600000),
    ("Royal Palm Flats", "Chennai", 5800000),
    ("Sapphire Towers", "Chennai", 6200000),

    ("Pearl Residency", "Hyderabad", 3400000),
    ("Golden Meadows", "Hyderabad", 3800000),
    ("Urban Elite Homes", "Hyderabad", 4500000),
    ("Silver Nest", "Hyderabad", 5100000),
    ("Twin Palms Residency", "Hyderabad", 5600000),

    ("Eastern Heights", "Kolkata", 3000000),
    ("Riverside View", "Kolkata", 3900000),
    ("Urban Heights", "Kolkata", 4100000),
    ("Emerald Residency", "Kolkata", 4600000),
    ("Magnolia Apartments", "Kolkata", 5300000),

    ("Metro Green Homes", "Lucknow", 2800000),
    ("Prime Residency", "Lucknow", 3300000),
    ("Rosewood Flats", "Lucknow", 3600000),
    ("Dream Valley Homes", "Lucknow", 4000000),
    ("Sapphire Residency", "Lucknow", 4500000),

    ("Pink City Flats", "Jaipur", 2900000),
    ("Royal Heritage Homes", "Jaipur", 3500000),
    ("Sunshine Residency", "Jaipur", 3800000),
    ("BlueStone Towers", "Jaipur", 4200000),
    ("Golden Leaf Apartments", "Jaipur", 4600000),

    ("City Center Apartment", "Ahmedabad", 3100000),
    ("Silverline Residency", "Ahmedabad", 3500000),
    ("Maple Towers", "Ahmedabad", 3900000),
    ("Crystal View Homes", "Ahmedabad", 4200000),
    ("Sunrise Enclave", "Ahmedabad", 4700000)
]

docs = []

for title, city, price in properties:
    docs.append({
        "title": title,
        "city": city,
        "price": price,
        "status": "available",
        "created_at": datetime.now(UTC)
    })

properties_col.insert_many(docs)

print("Inserted 50 properties successfully.")
