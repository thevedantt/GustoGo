from app import app, db
from models import CakeFlavor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_cake_flavors():
    # Single Flavors
    single_flavors = [
        {"name": "Vanilla Delight", "price_per_kg": 600, "category": "Single"},
        {"name": "Chocolate Fudge", "price_per_kg": 750, "category": "Single"},
        {"name": "Red Velvet", "price_per_kg": 900, "category": "Single"},
        {"name": "Black Forest", "price_per_kg": 850, "category": "Single"},
        {"name": "Butterscotch Bliss", "price_per_kg": 700, "category": "Single"},
        {"name": "Caramel Crunch", "price_per_kg": 800, "category": "Single"},
        {"name": "Strawberry Swirl", "price_per_kg": 750, "category": "Single"},
        {"name": "Blueberry Burst", "price_per_kg": 950, "category": "Single"},
        {"name": "Pineapple Paradise", "price_per_kg": 650, "category": "Single"},
        {"name": "Mango Magic", "price_per_kg": 800, "category": "Single"},
        {"name": "Coffee Mocha", "price_per_kg": 900, "category": "Single"},
        {"name": "Nutella Indulgence", "price_per_kg": 1100, "category": "Single"},
        {"name": "Pistachio Dream", "price_per_kg": 1000, "category": "Single"},
        {"name": "Almond Joy", "price_per_kg": 950, "category": "Single"},
        {"name": "Coconut Cream", "price_per_kg": 850, "category": "Single"},
        {"name": "Oreo Cookies & Cream", "price_per_kg": 950, "category": "Single"},
        {"name": "Matcha Green Tea", "price_per_kg": 1050, "category": "Single"},
        {"name": "Honey Almond", "price_per_kg": 900, "category": "Single"},
        {"name": "Lemon Zest", "price_per_kg": 750, "category": "Single"},
        {"name": "Raspberry Rose", "price_per_kg": 950, "category": "Single"},
        {"name": "Chocolate Truffle", "price_per_kg": 1000, "category": "Single"},
        {"name": "White Chocolate Delight", "price_per_kg": 1050, "category": "Single"},
        {"name": "Tiramisu Temptation", "price_per_kg": 1200, "category": "Single"},
        {"name": "Dark Chocolate Espresso", "price_per_kg": 1100, "category": "Single"},
        {"name": "Salted Caramel Bliss", "price_per_kg": 1000, "category": "Single"}
    ]

    # Flavor Combinations
    combination_flavors = [
        {"name": "Choco-Vanilla Fusion", "price_per_kg": 850, "category": "Combination"},
        {"name": "Strawberry Chocolate Drizzle", "price_per_kg": 900, "category": "Combination"},
        {"name": "Blueberry Cheesecake Delight", "price_per_kg": 1200, "category": "Combination"},
        {"name": "Mango Raspberry Swirl", "price_per_kg": 1100, "category": "Combination"},
        {"name": "Butterscotch Caramel Crunch", "price_per_kg": 900, "category": "Combination"},
        {"name": "Chocolate Peanut Butter", "price_per_kg": 1100, "category": "Combination"},
        {"name": "Red Velvet & White Chocolate", "price_per_kg": 1300, "category": "Combination"},
        {"name": "Lemon Blueberry Bliss", "price_per_kg": 1000, "category": "Combination"},
        {"name": "Coconut Pineapple Tropical", "price_per_kg": 850, "category": "Combination"},
        {"name": "Almond Pistachio Delight", "price_per_kg": 1200, "category": "Combination"},
        {"name": "Coffee Hazelnut Heaven", "price_per_kg": 1250, "category": "Combination"},
        {"name": "Oreo Choco Fudge", "price_per_kg": 1100, "category": "Combination"},
        {"name": "Chocolate Strawberry Fantasy", "price_per_kg": 1000, "category": "Combination"},
        {"name": "Nutella Banana Surprise", "price_per_kg": 1200, "category": "Combination"},
        {"name": "Carrot Walnut Spice", "price_per_kg": 950, "category": "Combination"},
        {"name": "Raspberry White Chocolate", "price_per_kg": 1300, "category": "Combination"},
        {"name": "Tiramisu Cheesecake Fusion", "price_per_kg": 1400, "category": "Combination"},
        {"name": "Choco-Mint Bliss", "price_per_kg": 1100, "category": "Combination"},
        {"name": "Dark Chocolate Raspberry Indulgence", "price_per_kg": 1300, "category": "Combination"},
        {"name": "Apple Cinnamon Caramel", "price_per_kg": 1000, "category": "Combination"},
        {"name": "Blackberry Lavender", "price_per_kg": 1300, "category": "Combination"},
        {"name": "Choco-Orange Zest", "price_per_kg": 1050, "category": "Combination"},
        {"name": "Vanilla Rose Petal", "price_per_kg": 850, "category": "Combination"},
        {"name": "Honey & Walnut Delight", "price_per_kg": 950, "category": "Combination"},
        {"name": "S'mores Sensation", "price_per_kg": 1200, "category": "Combination"}
    ]

    try:
        # Clear existing cake flavors
        CakeFlavor.query.delete()
        db.session.commit()
        logger.info("Cleared existing cake flavors")

        # Add single flavors
        for flavor in single_flavors:
            cake = CakeFlavor(**flavor)
            db.session.add(cake)
        logger.info(f"Added {len(single_flavors)} single flavors")

        # Add combination flavors
        for flavor in combination_flavors:
            cake = CakeFlavor(**flavor)
            db.session.add(cake)
        logger.info(f"Added {len(combination_flavors)} combination flavors")

        db.session.commit()
        logger.info("Successfully populated cake flavors database")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error populating cake flavors: {str(e)}")
        raise

if __name__ == '__main__':
    with app.app_context():
        populate_cake_flavors() 