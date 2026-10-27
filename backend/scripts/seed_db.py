"""Database seed script populating verified locations and pilot student profiles."""
import asyncio
import os
import sys

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.database import AsyncSessionLocal, init_db
from backend.app.models.location import Location
from backend.app.models.user import User
from backend.app.services.auth_service import hash_password

SEEDED_LOCATIONS = [
    {
        "id": "campus",
        "name": "MAHE Bengaluru Campus",
        "area": "Govindapura, Yelahanka",
        "kind": "campus",
        "corridor": "campus",
        "latitude": 13.1147,
        "longitude": 77.5958,
    },
    {
        "id": "gate",
        "name": "Campus South Gate",
        "area": "BSF Campus Road",
        "kind": "campus",
        "corridor": "campus",
        "latitude": 13.1118,
        "longitude": 77.5942,
    },
    {
        "id": "yelahanka",
        "name": "Yelahanka New Town Bus Stand",
        "area": "NES Junction, Yelahanka",
        "kind": "transit",
        "corridor": "north",
        "latitude": 13.0995,
        "longitude": 77.5969,
    },
    {
        "id": "hebbal",
        "name": "Hebbal Flyover / Esteem Mall",
        "area": "Bellary Road, Hebbal",
        "kind": "transit",
        "corridor": "central",
        "latitude": 13.0358,
        "longitude": 77.597,
    },
    {
        "id": "airport",
        "name": "Kempegowda International Airport (BLR)",
        "area": "Terminal 1 & 2, Devanahalli",
        "kind": "transit",
        "corridor": "airport",
        "latitude": 13.1986,
        "longitude": 77.7066,
    },
    {
        "id": "majestic",
        "name": "KSR Bengaluru (Majestic) Station",
        "area": "Kempegowda Bus Station",
        "kind": "transit",
        "corridor": "central",
        "latitude": 12.9778,
        "longitude": 77.5728,
    },
    {
        "id": "indiranagar",
        "name": "Indiranagar 100ft Road Metro",
        "area": "Indiranagar Stage 1",
        "kind": "commercial",
        "corridor": "central",
        "latitude": 12.9784,
        "longitude": 77.6408,
    },
    {
        "id": "phoenix",
        "name": "Phoenix Marketcity",
        "area": "Whitefield Main Road, Mahadevapura",
        "kind": "commercial",
        "corridor": "central",
        "latitude": 12.9959,
        "longitude": 77.6963,
    },
    {
        "id": "mg_road",
        "name": "MG Road Metro Station",
        "area": "Brigade Road / MG Road",
        "kind": "commercial",
        "corridor": "central",
        "latitude": 12.9756,
        "longitude": 77.6097,
    },
]

SEEDED_STUDENTS = [
    {
        "name": "Kkrish Verma",
        "email": "kkrish.verma@learner.manipal.edu",
        "area": "MAHE Campus",
        "role": "student",
    },
    {
        "name": "Sumukh J",
        "email": "sumukh.j@learner.manipal.edu",
        "area": "Yelahanka",
        "role": "student",
    },
    {
        "name": "Prathyush",
        "email": "prathyush@learner.manipal.edu",
        "area": "MAHE Campus",
        "role": "student",
    },
    {
        "name": "Ananya Sharma",
        "email": "ananya.sharma@learner.manipal.edu",
        "area": "Campus South Gate",
        "role": "student",
    },
    {
        "name": "Rahul Verma",
        "email": "rahul.verma@learner.manipal.edu",
        "area": "Yelahanka",
        "role": "student",
    },
    {
        "name": "Sneha Rao",
        "email": "sneha.rao@learner.manipal.edu",
        "area": "Hebbal",
        "role": "student",
    },
    {
        "name": "Campus Safety Officer",
        "email": "safety.officer@manipal.edu",
        "area": "Administrative Block",
        "role": "reviewer",
    },
]


async def seed():
    print("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Seed locations
        for loc in SEEDED_LOCATIONS:
            existing = await session.get(Location, loc["id"])
            if not existing:
                location_obj = Location(
                    id=loc["id"],
                    name=loc["name"],
                    area=loc["area"],
                    kind=loc["kind"],
                    corridor=loc["corridor"],
                    latitude=loc["latitude"],
                    longitude=loc["longitude"],
                    is_active=True,
                )
                session.add(location_obj)

        # Seed students
        from sqlalchemy import select
        for stu in SEEDED_STUDENTS:
            query = select(User).where(User.email == stu["email"])
            res = await session.execute(query)
            existing_user = res.scalar_one_or_none()
            if not existing_user:
                user_obj = User(
                    name=stu["name"],
                    email=stu["email"],
                    area=stu["area"],
                    role=stu["role"],
                    is_verified=True,
                    password_hash=hash_password("ManiPool@2026"),
                )
                session.add(user_obj)

        await session.commit()
        print(f"Successfully seeded {len(SEEDED_LOCATIONS)} locations and {len(SEEDED_STUDENTS)} verified accounts.")


if __name__ == "__main__":
    asyncio.run(seed())
