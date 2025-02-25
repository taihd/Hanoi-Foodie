"""Script to add records to the database from JSON files."""
import os
import json
import psycopg2
from psycopg2.extras import DictCursor
import logging
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "5432")
}

def load_data() -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Load data from JSON files."""
    with open('data/restaurants.json', 'r', encoding='utf-8') as f:
        restaurants = json.load(f)
    
    with open('data/dishes.json', 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    
    with open('data/restaurant_dishes.json', 'r', encoding='utf-8') as f:
        restaurant_dishes = json.load(f)
    
    return restaurants, dishes, restaurant_dishes

def add_records() -> None:
    """Add records from JSON files to the database."""
    try:
        restaurants, dishes, restaurant_dishes = load_data()
        conn = psycopg2.connect(**DB_CONFIG)
        
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Add restaurants
            restaurants_dict = {}
            for restaurant in restaurants:
                logger.info(f"Adding restaurant: {restaurant['name']}")
                cursor.execute("""
                    INSERT INTO restaurants (name, address, website, google_url, rating, 
                                          phone, opening_hours, images, notes)
                    VALUES (%(name)s, %(address)s, %(website)s, %(google_url)s, %(rating)s, 
                           %(phone)s, %(opening_hours)s, %(images)s, %(notes)s)
                    RETURNING id
                """, restaurant)
                restaurants_dict[restaurant['name']] = cursor.fetchone()[0]

            # Add dishes
            dishes_dict = {}
            for dish in dishes:
                logger.info(f"Adding dish: {dish['name']}")
                cursor.execute("""
                    INSERT INTO dishes (name, description, images, notes)
                    VALUES (%(name)s, %(description)s, %(images)s, %(notes)s)
                    RETURNING id
                """, dish)
                dishes_dict[dish['name']] = cursor.fetchone()[0]

            # Create relationships with prices
            for rel in restaurant_dishes:
                logger.info(f"Adding menu item: {rel['dish']} to {rel['restaurant']}")
                cursor.execute("""
                    INSERT INTO restaurant_dishes (restaurant_id, dish_id, price)
                    VALUES (%s, %s, %s)
                """, (restaurants_dict[rel['restaurant']], 
                     dishes_dict[rel['dish']], 
                     rel['price']))

            conn.commit()
            logger.info("Successfully added all records to database")

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_records() 