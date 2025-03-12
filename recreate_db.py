import sqlite3
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_database():
    """Recreate the SQLite database"""
    try:
        logger.info("Starting database recreation...")
        
        # Ensure instance directory exists
        if not os.path.exists('instance'):
            os.makedirs('instance')
            logger.info("Created instance directory")
        
        # Database file path
        db_file = 'instance/gustogo.db'
        
        # Remove existing database file if it exists
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                logger.info(f"Removed existing database file: {db_file}")
            except Exception as e:
                logger.error(f"Error removing database file: {str(e)}")
                raise
        
        # Create new database and tables
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create cart_items table with all necessary columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cart_id INTEGER NOT NULL,
                item_type VARCHAR(20) NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                size_kg FLOAT,
                message TEXT,
                special_instructions TEXT,
                customization_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create carts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database recreation completed successfully")
        
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        raise

if __name__ == '__main__':
    recreate_database() 