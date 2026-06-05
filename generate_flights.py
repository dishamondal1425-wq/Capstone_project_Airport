import pandas as pd
import random

# Airports / Cities
cities = [
    "Kolkata",
    "Delhi",
    "Mumbai",
    "Chennai",
    "Bangalore",
    "Hyderabad",
    "Pune",
    "Ahmedabad",
    "Goa",
    "Jaipur",
    "Lucknow"
]

statuses = [
    "Boarding",
    "Delayed",
    "On Time",
    "Cancelled"
]

flights = []

for i in range(1000):

    airline = random.choice([
        "AI",
        "6E",
        "UK",
        "SG",
        "QP"
    ])

    flight_number = (
        airline +
        str(random.randint(100, 999))
    )

    # Source & Destination
    source = random.choice(cities)

    destination = random.choice(cities)

    # Prevent same city
    while source == destination:
        destination = random.choice(
            cities
        )

    # Time
    hour = random.randint(0, 23)

    minute = random.choice([
        "00",
        "15",
        "30",
        "45"
    ])

    flight_time = (
        f"{hour:02}:{minute}"
    )

    status = random.choice(
        statuses
    )

    gate = random.randint(
        1, 20
    )

    price = random.randint(
        3000, 12000
    )

    flights.append([
        flight_number,
        source,
        destination,
        flight_time,
        status,
        gate,
        price
    ])

df = pd.DataFrame(
    flights,
    columns=[
        "flight_no",
        "source",
        "destination",
        "time",
        "status",
        "gate",
        "price"
    ]
)

df.to_csv(
    "database/flights.csv",
    index=False
)

print(
    "1000 flights created!"
)