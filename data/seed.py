"""
Seed Data Script

Populates the database with sample ports, ships, and zones.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings


# Major world ports
PORTS = [
    {"locode": "SGSIN", "name": "Singapore", "country_code": "SG", "latitude": 1.29, "longitude": 103.85, "is_major": True},
    {"locode": "NLRTM", "name": "Rotterdam", "country_code": "NL", "latitude": 51.95, "longitude": 4.48, "is_major": True},
    {"locode": "CNSHA", "name": "Shanghai", "country_code": "CN", "latitude": 31.23, "longitude": 121.47, "is_major": True},
    {"locode": "AEJEA", "name": "Jebel Ali", "country_code": "AE", "latitude": 25.02, "longitude": 55.06, "is_major": True},
    {"locode": "HKHKG", "name": "Hong Kong", "country_code": "HK", "latitude": 22.32, "longitude": 114.17, "is_major": True},
    {"locode": "KRPUS", "name": "Busan", "country_code": "KR", "latitude": 35.10, "longitude": 129.03, "is_major": True},
    {"locode": "DEHAM", "name": "Hamburg", "country_code": "DE", "latitude": 53.55, "longitude": 9.99, "is_major": True},
    {"locode": "USNYC", "name": "New York", "country_code": "US", "latitude": 40.71, "longitude": -74.01, "is_major": True},
    {"locode": "USLAX", "name": "Los Angeles", "country_code": "US", "latitude": 33.74, "longitude": -118.26, "is_major": True},
    {"locode": "JPYOK", "name": "Yokohama", "country_code": "JP", "latitude": 35.44, "longitude": 139.64, "is_major": True},
    {"locode": "TWKHH", "name": "Kaohsiung", "country_code": "TW", "latitude": 22.62, "longitude": 120.30, "is_major": True},
    {"locode": "MYPKG", "name": "Port Klang", "country_code": "MY", "latitude": 3.00, "longitude": 101.40, "is_major": True},
    {"locode": "EGPSD", "name": "Port Said", "country_code": "EG", "latitude": 31.26, "longitude": 32.30, "is_major": True},
    {"locode": "GBFXT", "name": "Felixstowe", "country_code": "GB", "latitude": 51.95, "longitude": 1.35, "is_major": True},
    {"locode": "ESALG", "name": "Algeciras", "country_code": "ES", "latitude": 36.13, "longitude": -5.45, "is_major": True},
]

# Sample ship profiles
SHIPS = [
    {
        "id": "container_large",
        "imo_number": "9876543",
        "name": "Ever Forward",
        "ship_type": "container",
        "length_overall": 400,
        "beam": 59,
        "draft_design": 14.5,
        "draft_max": 16.0,
        "deadweight": 200000,
        "engine_power": 80000,
        "design_speed": 24,
        "service_speed": 20,
        "min_speed": 10,
        "max_speed": 25,
        "sfc_design": 170,
        "fuel_type": "VLSFO",
        "block_coefficient": 0.65,
    },
    {
        "id": "tanker_vlcc",
        "imo_number": "9876544",
        "name": "Sea Champion",
        "ship_type": "tanker",
        "length_overall": 333,
        "beam": 60,
        "draft_design": 22,
        "draft_max": 23.5,
        "deadweight": 300000,
        "engine_power": 36000,
        "design_speed": 15,
        "service_speed": 13,
        "min_speed": 8,
        "max_speed": 16,
        "sfc_design": 180,
        "fuel_type": "VLSFO",
        "block_coefficient": 0.82,
    },
    {
        "id": "bulk_capesize",
        "imo_number": "9876545",
        "name": "Ocean Giant",
        "ship_type": "bulk_carrier",
        "length_overall": 300,
        "beam": 50,
        "draft_design": 18,
        "draft_max": 19.5,
        "deadweight": 180000,
        "engine_power": 20000,
        "design_speed": 14,
        "service_speed": 12,
        "min_speed": 8,
        "max_speed": 15,
        "sfc_design": 185,
        "fuel_type": "VLSFO",
        "block_coefficient": 0.85,
    },
]


async def seed_database():
    """Seed the database with sample data using raw SQL."""
    engine = create_async_engine(settings.database_url, echo=False)
    
    # Import models to create tables
    from app.models.base import Base
    from app.models import Port, ShipProfile, StormZone, PiracyZone
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        now = datetime.now()
        
        # Add ports
        print("Seeding ports...")
        for port_data in PORTS:
            port = Port(id=str(uuid4()), **port_data)
            session.add(port)

        # Add ships
        print("Seeding ship profiles...")
        for ship_data in SHIPS:
            ship = ShipProfile(**ship_data)
            session.add(ship)

        # Add storm zones
        print("Seeding storm zones...")
        storm1 = StormZone(
            id=str(uuid4()),
            name="Tropical Storm Alpha",
            storm_type="tropical_cyclone",
            center_latitude=15.5,
            center_longitude=-60.2,
            radius_nm=150,
            max_wind_speed=65,
            category=1,
            risk_level=0.8,
            valid_from=now,
            valid_until=now + timedelta(days=5),
        )
        session.add(storm1)

        storm2 = StormZone(
            id=str(uuid4()),
            name="Typhoon Beta",
            storm_type="typhoon",
            center_latitude=22.3,
            center_longitude=125.5,
            radius_nm=200,
            max_wind_speed=130,
            category=4,
            risk_level=0.95,
            valid_from=now,
            valid_until=now + timedelta(days=5),
        )
        session.add(storm2)

        # Add piracy zones
        print("Seeding piracy zones...")
        piracy1 = PiracyZone(
            id=str(uuid4()),
            name="Gulf of Aden HRA",
            region="Gulf of Aden",
            min_latitude=10,
            max_latitude=15,
            min_longitude=43,
            max_longitude=54,
            risk_level=0.7,
            incident_count=12,
            valid_from=now,
        )
        session.add(piracy1)

        piracy2 = PiracyZone(
            id=str(uuid4()),
            name="Strait of Malacca",
            region="Southeast Asia",
            min_latitude=0,
            max_latitude=6,
            min_longitude=95,
            max_longitude=105,
            risk_level=0.4,
            incident_count=8,
            valid_from=now,
        )
        session.add(piracy2)

        piracy3 = PiracyZone(
            id=str(uuid4()),
            name="Gulf of Guinea",
            region="West Africa",
            min_latitude=-2,
            max_latitude=8,
            min_longitude=-5,
            max_longitude=10,
            risk_level=0.85,
            incident_count=45,
            valid_from=now,
        )
        session.add(piracy3)

        await session.commit()
        print("Database seeded successfully!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
