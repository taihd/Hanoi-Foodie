"""Restaurant & Dish Explorer Streamlit App"""
import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)

def load_data():
    """Load all data from database."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Get restaurants
            cursor.execute("""
                SELECT id, name, address, website, google_url, rating, 
                       phone, opening_hours, images, notes
                FROM restaurants
            """)
            restaurants = [dict(r) for r in cursor.fetchall()]
            
            # Get dishes
            cursor.execute("""
                SELECT id, name, description, images, notes
                FROM dishes
            """)
            dishes = [dict(d) for d in cursor.fetchall()]
            
            # Get restaurant-dish relationships
            cursor.execute("""
                SELECT r.name as restaurant, d.name as dish, rd.price
                FROM restaurant_dishes rd
                JOIN restaurants r ON rd.restaurant_id = r.id
                JOIN dishes d ON rd.dish_id = d.id
            """)
            restaurant_dishes = [dict(rd) for rd in cursor.fetchall()]
            
    return restaurants, dishes, restaurant_dishes

def get_restaurants_by_dish(dish_name: str, restaurants: List[Dict], relations: List[Dict]) -> List[Dict]:
    """Get all restaurants that serve a specific dish."""
    restaurant_names = [r["restaurant"] for r in relations if r["dish"] == dish_name]
    return [r for r in restaurants if r["name"] in restaurant_names]

def get_dishes_by_restaurant(restaurant_name: str, dishes: List[Dict], relations: List[Dict]) -> List[Dict]:
    """Get all dishes served by a specific restaurant."""
    dish_names = [r["dish"] for r in relations if r["restaurant"] == restaurant_name]
    return [d for d in dishes if d["name"] in dish_names]

def get_price(restaurant_name: str, dish_name: str, relations: List[Dict]) -> int:
    """Get the price of a dish at a specific restaurant."""
    for r in relations:
        if r["restaurant"] == restaurant_name and r["dish"] == dish_name:
            return r["price"]
    return 0

def main():
    st.title("🍜 Hanoi Foodie")
    
    # Load data
    restaurants, dishes, restaurant_dishes = load_data()
    
    # Add custom CSS for image styling
    st.markdown("""
        <style>
            img {
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                margin: 10px 0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for different exploration methods
    tab1, tab2 = st.tabs(["Explore by Dish", "Explore by Restaurant"])
    
    with tab1:
        st.header("Explore Restaurants by Dish")
        
        # Create dish selector
        dish_names = sorted([dish["name"] for dish in dishes])
        selected_dish = st.selectbox("Select a Dish", dish_names)
        
        if selected_dish:
            # Get the dish details
            dish_info = next((d for d in dishes if d["name"] == selected_dish), None)
            
            # Display dish details
            st.subheader(f"About {selected_dish}")
            st.write(dish_info['description'])
            
            # Display dish images if available
            images = dish_info.get('images', [])
            if images:
                try:
                    # Create a container for images
                    image_container = st.container()
                    with image_container:
                        cols = st.columns(2)  # Display 2 images per row
                        for i, img_url in enumerate(images):
                            with cols[i % 2]:
                                st.image(
                                    img_url,
                                    use_container_width=True,
                                    output_format="JPEG"
                                )
                except Exception as e:
                    st.error(f"Error loading images: {str(e)}")
            else:
                st.info("No images available for this dish")
            
            if dish_info.get('notes'):
                st.write(f"**Notes:** {dish_info['notes']}")
            
            # Get restaurants serving this dish
            restaurants_with_dish = get_restaurants_by_dish(selected_dish, restaurants, restaurant_dishes)
            
            # Display restaurants
            st.subheader(f"Restaurants serving {selected_dish}")
            
            if restaurants_with_dish:
                for restaurant in restaurants_with_dish:
                    # Create an expander for each restaurant
                    price = get_price(restaurant['name'], selected_dish, restaurant_dishes)
                    with st.expander(f"{restaurant['name']} - ₫{price:,}"):
                        col1, col2 = st.columns(2)
                        
                        if restaurant.get('address'):
                            col1.write(f"**Address:** {restaurant['address']}")
                        if restaurant.get('phone'):
                            col1.write(f"**Phone:** {restaurant['phone']}")
                        
                        if restaurant.get('rating'):
                            col2.write(f"**Rating:** {restaurant['rating']}/5")
                        if restaurant.get('opening_hours'):
                            col2.write(f"**Hours:** {restaurant['opening_hours']}")
                        
                        if restaurant.get('website'):
                            st.markdown(f"[Visit Website]({restaurant['website']})")
                        
                        if restaurant.get('google_url'):
                            st.markdown(f"[View on Google]({restaurant['google_url']})")
            else:
                st.info(f"No restaurants currently serve {selected_dish}")
    
    with tab2:
        st.header("Explore Dishes by Restaurant")
        
        # Create restaurant selector
        restaurant_names = sorted([r["name"] for r in restaurants])
        selected_restaurant = st.selectbox("Select a Restaurant", restaurant_names)
        
        if selected_restaurant:
            # Get the restaurant details
            restaurant_info = next((r for r in restaurants if r["name"] == selected_restaurant), None)
            
            # Display restaurant details
            st.subheader(f"About {selected_restaurant}")
            
            # Display restaurant images if available
            images = restaurant_info.get('images', [])
            if images:
                try:
                    image_container = st.container()
                    with image_container:
                        cols = st.columns(2)
                        for i, img_url in enumerate(images):
                            with cols[i % 2]:
                                st.image(
                                    img_url,
                                    use_container_width=True,
                                    output_format="JPEG"
                                )
                except Exception as e:
                    st.error(f"Error loading images: {str(e)}")
            else:
                st.info("No images available for this restaurant")
            
            col1, col2 = st.columns(2)
            
            if restaurant_info.get('address'):
                col1.write(f"**Address:** {restaurant_info['address']}")
            if restaurant_info.get('phone'):
                col1.write(f"**Phone:** {restaurant_info['phone']}")
            
            if restaurant_info.get('rating'):
                col2.write(f"**Rating:** {restaurant_info['rating']}/5")
            if restaurant_info.get('opening_hours'):
                col2.write(f"**Hours:** {restaurant_info['opening_hours']}")
            
            if restaurant_info.get('notes'):
                st.write(f"**Notes:** {restaurant_info['notes']}")
            
            if restaurant_info.get('website'):
                st.markdown(f"[Visit Website]({restaurant_info['website']})")
            
            if restaurant_info.get('google_url'):
                st.markdown(f"[View on Google]({restaurant_info['google_url']})")
            
            # Get dishes at this restaurant
            dishes_at_restaurant = get_dishes_by_restaurant(selected_restaurant, dishes, restaurant_dishes)
            
            # Display dishes
            st.subheader(f"Menu at {selected_restaurant}")
            
            if dishes_at_restaurant:
                for dish in dishes_at_restaurant:
                    # Create an expander for each dish
                    price = get_price(selected_restaurant, dish['name'], restaurant_dishes)
                    with st.expander(f"{dish['name']} - ₫{price:,}"):
                        images = dish.get('images', [])
                        if images:
                            try:
                                image_container = st.container()
                                with image_container:
                                    cols = st.columns(2)
                                    for i, img_url in enumerate(images):
                                        with cols[i % 2]:
                                            st.image(
                                                img_url,
                                                use_container_width=True,
                                                output_format="JPEG"
                                            )
                            except Exception as e:
                                st.error(f"Error loading images: {str(e)}")
                        else:
                            st.info("No images available for this dish")
                        
                        if dish.get('description'):
                            st.write(f"**Description:** {dish['description']}")
                        if dish.get('notes'):
                            st.write(f"**Notes:** {dish['notes']}")
            else:
                st.info(f"No dishes available at {selected_restaurant}")

if __name__ == "__main__":
    main() 