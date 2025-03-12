from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
from models import Category, MenuItem, CakeFlavor, MenuSession, CakeSession

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database engines
menu_engine = create_engine('sqlite:///instance/menu_db.db')
cake_engine = create_engine('sqlite:///instance/cakes_db.db')

# Create session factories
MenuSession = sessionmaker(bind=menu_engine)
CakeSession = sessionmaker(bind=cake_engine)

def init_menu_db():
    """Initialize the menu database with sample data"""
    try:
        logger.info("Starting menu database initialization...")
        with MenuSession() as session:
            # Drop and recreate tables
            Category.__table__.drop(menu_engine, checkfirst=True)
            MenuItem.__table__.drop(menu_engine, checkfirst=True)
            Category.__table__.create(menu_engine)
            MenuItem.__table__.create(menu_engine)
            
            # Add categories
            categories = [
                Category(name='Appetizers'),
                Category(name='Main Course'),
                Category(name='Desserts'),
                Category(name='Beverages'),
                Category(name='Combos')
            ]
            session.add_all(categories)
            session.commit()
            
            # Get category IDs
            appetizers = session.query(Category).filter_by(name='Appetizers').first()
            main_course = session.query(Category).filter_by(name='Main Course').first()
            desserts = session.query(Category).filter_by(name='Desserts').first()
            beverages = session.query(Category).filter_by(name='Beverages').first()
            combos = session.query(Category).filter_by(name='Combos').first()
            
            # Appetizers
            appetizer_items = [
                MenuItem(name='Spring Rolls', description='Crispy rolls filled with vegetables', price=180, category_id=appetizers.id),
                MenuItem(name='Chicken Wings', description='Spicy chicken wings with sauce', price=250, category_id=appetizers.id),
                MenuItem(name='Paneer Tikka', description='Marinated and grilled cottage cheese', price=220, category_id=appetizers.id),
                MenuItem(name='Onion Rings', description='Crispy battered onion rings', price=150, category_id=appetizers.id),
                MenuItem(name='Mozzarella Sticks', description='Breaded cheese sticks with marinara', price=200, category_id=appetizers.id),
                MenuItem(name='Bruschetta', description='Toasted bread with tomatoes and herbs', price=180, category_id=appetizers.id),
                MenuItem(name='Nachos', description='Tortilla chips with cheese and toppings', price=220, category_id=appetizers.id),
                MenuItem(name='Samosa', description='Crispy pastry with spiced filling', price=120, category_id=appetizers.id),
                MenuItem(name='French Fries', description='Crispy golden fries', price=100, category_id=appetizers.id),
                MenuItem(name='Garlic Bread', description='Toasted bread with garlic butter', price=120, category_id=appetizers.id)
            ]
            
            # Main Course
            main_course_items = [
                MenuItem(name='Butter Chicken', description='Tender chicken in rich tomato sauce', price=350, category_id=main_course.id),
                MenuItem(name='Dal Makhani', description='Creamy black lentils', price=280, category_id=main_course.id),
                MenuItem(name='Veg Biryani', description='Fragrant rice with mixed vegetables', price=300, category_id=main_course.id),
                MenuItem(name='Paneer Butter Masala', description='Cottage cheese in rich gravy', price=320, category_id=main_course.id),
                MenuItem(name='Chicken Tikka Masala', description='Grilled chicken in spiced sauce', price=340, category_id=main_course.id),
                MenuItem(name='Palak Paneer', description='Cottage cheese in spinach gravy', price=300, category_id=main_course.id),
                MenuItem(name='Fish Curry', description='Fresh fish in coconut gravy', price=380, category_id=main_course.id),
                MenuItem(name='Mushroom Masala', description='Mushrooms in spiced gravy', price=280, category_id=main_course.id),
                MenuItem(name='Chicken Korma', description='Chicken in rich cream sauce', price=360, category_id=main_course.id),
                MenuItem(name='Veg Korma', description='Mixed vegetables in cream sauce', price=300, category_id=main_course.id)
            ]
            
            # Desserts
            dessert_items = [
                MenuItem(name='Gulab Jamun', description='Sweet milk dumplings in sugar syrup', price=120, category_id=desserts.id),
                MenuItem(name='Ice Cream', description='Vanilla ice cream with toppings', price=150, category_id=desserts.id),
                MenuItem(name='Rasmalai', description='Soft cottage cheese in sweet milk', price=130, category_id=desserts.id),
                MenuItem(name='Kheer', description='Sweet rice pudding', price=100, category_id=desserts.id),
                MenuItem(name='Jalebi', description='Crispy sweet pretzels', price=120, category_id=desserts.id),
                MenuItem(name='Fruit Custard', description='Mixed fruits in vanilla custard', price=140, category_id=desserts.id),
                MenuItem(name='Rasgulla', description='Soft cottage cheese balls in syrup', price=110, category_id=desserts.id),
                MenuItem(name='Kulfi', description='Traditional Indian ice cream', price=130, category_id=desserts.id),
                MenuItem(name='Zarda', description='Sweet saffron rice', price=160, category_id=desserts.id),
                MenuItem(name='Faluda', description='Sweet vermicelli dessert', price=120, category_id=desserts.id)
            ]
            
            # Beverages
            beverage_items = [
                MenuItem(name='Cold Coffee', description='Rich cold coffee with ice cream', price=180, category_id=beverages.id),
                MenuItem(name='Fresh Lime Soda', description='Refreshing lime drink', price=80, category_id=beverages.id),
                MenuItem(name='Mango Shake', description='Fresh mango milkshake', price=150, category_id=beverages.id),
                MenuItem(name='Masala Chai', description='Spiced Indian tea', price=60, category_id=beverages.id),
                MenuItem(name='Lassi', description='Sweet yogurt drink', price=100, category_id=beverages.id),
                MenuItem(name='Fruit Smoothie', description='Mixed fruit smoothie', price=160, category_id=beverages.id),
                MenuItem(name='Green Tea', description='Fresh green tea', price=70, category_id=beverages.id),
                MenuItem(name='Buttermilk', description='Spiced buttermilk', price=50, category_id=beverages.id),
                MenuItem(name='Orange Juice', description='Fresh orange juice', price=120, category_id=beverages.id),
                MenuItem(name='Watermelon Juice', description='Fresh watermelon juice', price=100, category_id=beverages.id)
            ]
            
            # Combos
            combo_items = [
                MenuItem(name='Family Feast', description='Complete meal for 4 people', price=1200, category_id=combos.id),
                MenuItem(name='Couple Special', description='Romantic dinner for two', price=800, category_id=combos.id),
                MenuItem(name='Lunch Box', description='Complete lunch with dessert', price=400, category_id=combos.id),
                MenuItem(name='Party Pack', description='Food for 8-10 people', price=2000, category_id=combos.id),
                MenuItem(name='Weekend Brunch', description='Special brunch menu for two', price=900, category_id=combos.id),
                MenuItem(name='Kids Special', description='Kid-friendly meal with dessert', price=300, category_id=combos.id),
                MenuItem(name='Office Lunch', description='Group lunch for 5 people', price=1500, category_id=combos.id),
                MenuItem(name='Festival Special', description='Special menu for celebrations', price=2500, category_id=combos.id),
                MenuItem(name='Quick Bite', description='Light meal for one', price=250, category_id=combos.id),
                MenuItem(name='Healthy Choice', description='Low-calorie balanced meal', price=350, category_id=combos.id)
            ]
            
            # Add all menu items
            session.add_all(appetizer_items)
            session.add_all(main_course_items)
            session.add_all(dessert_items)
            session.add_all(beverage_items)
            session.add_all(combo_items)
            
            session.commit()
            logger.info("Menu database initialized successfully")
            
    except Exception as e:
        logger.error(f"Error initializing menu database: {str(e)}")
        raise

def init_cake_db():
    """Initialize the cake database with sample data"""
    try:
        logger.info("Starting cake database initialization...")
        with CakeSession() as session:
            # Drop and recreate tables
            CakeFlavor.__table__.drop(cake_engine, checkfirst=True)
            CakeFlavor.__table__.create(cake_engine)
            
            # Single Flavors
            single_flavors = [
                CakeFlavor(name="Classic Vanilla", description="Pure vanilla bean flavor", price_per_kg=500, category="Single"),
                CakeFlavor(name="Rich Chocolate", description="Deep, dark chocolate", price_per_kg=550, category="Single"),
                CakeFlavor(name="Fresh Strawberry", description="Real strawberry flavor", price_per_kg=600, category="Single"),
                CakeFlavor(name="Butter Pecan", description="Buttery vanilla with toasted pecans", price_per_kg=550, category="Single"),
                CakeFlavor(name="Coffee", description="Rich coffee flavor", price_per_kg=500, category="Single"),
                CakeFlavor(name="Mint Chocolate", description="Cool mint with chocolate", price_per_kg=550, category="Single"),
                CakeFlavor(name="Red Velvet", description="Classic red velvet", price_per_kg=600, category="Single"),
                CakeFlavor(name="Carrot", description="Spiced carrot cake", price_per_kg=550, category="Single"),
                CakeFlavor(name="Lemon", description="Fresh lemon flavor", price_per_kg=500, category="Single"),
                CakeFlavor(name="Coconut", description="Tropical coconut flavor", price_per_kg=550, category="Single"),
                CakeFlavor(name="Pistachio", description="Nutty pistachio flavor", price_per_kg=600, category="Single"),
                CakeFlavor(name="Banana", description="Ripe banana flavor", price_per_kg=500, category="Single"),
                CakeFlavor(name="Orange", description="Fresh orange flavor", price_per_kg=550, category="Single"),
                CakeFlavor(name="Almond", description="Pure almond flavor", price_per_kg=600, category="Single"),
                CakeFlavor(name="Peanut Butter", description="Rich peanut butter flavor", price_per_kg=550, category="Single"),
                CakeFlavor(name="Maple", description="Pure maple flavor", price_per_kg=600, category="Single"),
                CakeFlavor(name="Hazelnut", description="Roasted hazelnut flavor", price_per_kg=550, category="Single"),
                CakeFlavor(name="Raspberry", description="Fresh raspberry flavor", price_per_kg=600, category="Single"),
                CakeFlavor(name="Blueberry", description="Sweet blueberry flavor", price_per_kg=550, category="Single"),
                CakeFlavor(name="Mango", description="Tropical mango flavor", price_per_kg=600, category="Single"),
                CakeFlavor(name="Pineapple", description="Fresh pineapple flavor", price_per_kg=550, category="Single"),
                CakeFlavor(name="Cherry", description="Sweet cherry flavor", price_per_kg=600, category="Single"),
                CakeFlavor(name="Walnut", description="Nutty walnut flavor", price_per_kg=550, category="Single"),
                CakeFlavor(name="Cinnamon", description="Warm cinnamon flavor", price_per_kg=500, category="Single"),
                CakeFlavor(name="Ginger", description="Spiced ginger flavor", price_per_kg=550, category="Single")
            ]
            
            # Combination Flavors
            combination_flavors = [
                CakeFlavor(name="Chocolate Vanilla Swirl", description="Swirl of chocolate and vanilla", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Strawberry Chocolate", description="Strawberry and chocolate layers", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Coffee Toffee", description="Coffee with toffee bits", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Mint Chocolate Chip", description="Mint with chocolate chips", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Red Velvet Cheesecake", description="Red velvet with cheesecake swirl", price_per_kg=700, category="Combination"),
                CakeFlavor(name="Carrot Walnut", description="Carrot cake with walnuts", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Lemon Blueberry", description="Lemon with blueberry swirl", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Coconut Pineapple", description="Coconut with pineapple chunks", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Pistachio Almond", description="Pistachio with almond pieces", price_per_kg=700, category="Combination"),
                CakeFlavor(name="Banana Chocolate", description="Banana with chocolate chips", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Orange Cranberry", description="Orange with dried cranberries", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Almond Raspberry", description="Almond with raspberry swirl", price_per_kg=700, category="Combination"),
                CakeFlavor(name="Peanut Butter Chocolate", description="Peanut butter with chocolate", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Maple Pecan", description="Maple with toasted pecans", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Hazelnut Coffee", description="Hazelnut with coffee swirl", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Raspberry White Chocolate", description="Raspberry with white chocolate", price_per_kg=700, category="Combination"),
                CakeFlavor(name="Blueberry Lemon", description="Blueberry with lemon zest", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Mango Coconut", description="Mango with coconut flakes", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Pineapple Carrot", description="Pineapple with carrot pieces", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Cherry Almond", description="Cherry with almond pieces", price_per_kg=700, category="Combination"),
                CakeFlavor(name="Walnut Maple", description="Walnut with maple swirl", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Cinnamon Apple", description="Cinnamon with apple pieces", price_per_kg=600, category="Combination"),
                CakeFlavor(name="Ginger Lemon", description="Ginger with lemon zest", price_per_kg=650, category="Combination"),
                CakeFlavor(name="Chocolate Raspberry", description="Chocolate with raspberry swirl", price_per_kg=700, category="Combination"),
                CakeFlavor(name="Vanilla Strawberry", description="Vanilla with strawberry pieces", price_per_kg=650, category="Combination")
            ]
            
            # Add all flavors to session
            session.add_all(single_flavors)
            session.add_all(combination_flavors)
            
            # Commit changes
            session.commit()
            logger.info("Cake database initialized successfully")
            
    except Exception as e:
        logger.error(f"Error initializing cake database: {str(e)}")
        raise

def init_databases():
    """Initialize all databases"""
    try:
        logger.info("Starting database initialization...")
        init_menu_db()
        init_cake_db()
        logger.info("All databases initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize databases: {str(e)}")
        raise

if __name__ == '__main__':
    init_databases() 