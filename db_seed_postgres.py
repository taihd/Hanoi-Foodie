"""Script to populate the PostgreSQL database with sample data."""
import os
import json
import psycopg2
from psycopg2.extras import DictCursor
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters from environment variables
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "5432")
}

def load_sample_data() -> tuple[List[Dict], List[Dict], List[Dict]]:
    """Load sample data from JSON files."""
    with open('data/restaurants.json', 'r', encoding='utf-8') as f:
        restaurants = json.load(f)
    
    with open('data/dishes.json', 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    
    with open('data/restaurant_dishes.json', 'r', encoding='utf-8') as f:
        restaurant_dishes = json.load(f)
    
    return restaurants, dishes, restaurant_dishes

def create_tables(cursor) -> None:
    """Create the necessary tables if they don't exist."""
    logger.info("Creating tables...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            address TEXT NOT NULL,
            website TEXT,
            google_url TEXT,
            rating FLOAT,
            phone VARCHAR(20),
            opening_hours VARCHAR(100),
            images TEXT[],
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dishes (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            images TEXT[],
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurant_dishes (
            restaurant_id INTEGER REFERENCES restaurants(id),
            dish_id INTEGER REFERENCES dishes(id),
            price INTEGER NOT NULL,
            PRIMARY KEY (restaurant_id, dish_id)
        )
    """)

def seed_database(add_sample_data: bool = True) -> None:
    """Populate the database with sample data."""
    try:
        restaurants, dishes, restaurant_dishes = load_sample_data()
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Create tables
            create_tables(cursor)
            
            # Clear existing data
            cursor.execute("TRUNCATE restaurants, dishes, restaurant_dishes CASCADE")
            
            if add_sample_data:
                # Add restaurants
                restaurants_dict = {}
                for restaurant in restaurants:
                    cursor.execute("""
                        INSERT INTO restaurants (name, address, website, google_url, rating, phone, opening_hours, images, notes)
                        VALUES (%(name)s, %(address)s, %(website)s, %(google_url)s, %(rating)s, %(phone)s, %(opening_hours)s, %(images)s, %(notes)s)
                        RETURNING id
                    """, restaurant)
                    restaurants_dict[restaurant['name']] = cursor.fetchone()[0]

                # Add dishes
                dishes_dict = {}
                for dish in dishes:
                    cursor.execute("""
                        INSERT INTO dishes (name, description, images, notes)
                        VALUES (%(name)s, %(description)s, %(images)s, %(notes)s)
                        RETURNING id
                    """, dish)
                    dishes_dict[dish['name']] = cursor.fetchone()[0]

                # Create relationships with prices
                for rel in restaurant_dishes:
                    cursor.execute("""
                        INSERT INTO restaurant_dishes (restaurant_id, dish_id, price)
                        VALUES (%s, %s, %s)
                    """, (restaurants_dict[rel['restaurant']], dishes_dict[rel['dish']], rel['price']))

            conn.commit()
            logger.info("Database seeded successfully")

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database(add_sample_data=False) 