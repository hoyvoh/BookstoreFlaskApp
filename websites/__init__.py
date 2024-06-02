from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text, func
from os import path
import pandas as pd
from sqlalchemy import inspect, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

db = SQLAlchemy()

DB_NAME = "database.db"
        

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'thesecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    app.register_blueprint(views, url_prefix='/')

    from .model import Invoice, Product, Invoice_Details
    
    with app.app_context():
        if path.exists('./'+DB_NAME):
            print("Database exists at {}".format("./"+DB_NAME))
            db.drop_all()
        if True: 
            db.create_all()
            
            # See tables
            print(inspect(db.engine).get_table_names())

            # Create the trigger after creating the table
            trigger_sql = '''
            CREATE TRIGGER ignore_duplicate_pid
            BEFORE INSERT ON product
            FOR EACH ROW
            WHEN EXISTS (SELECT 1 FROM product WHERE pid = NEW.pid)
            BEGIN
                SELECT RAISE(IGNORE);
            END;
            '''
            db.session.execute(text(trigger_sql))
            db.session.commit()

            # for each new product added in the invoice details
            # the invoice increase
            trigger_invoice_add = '''
            CREATE TRIGGER update_invoice_add
            AFTER INSERT ON invoice_details
            FOR EACH ROW
            BEGIN
                UPDATE Invoice
                SET total_amount = total_amount + (NEW.unit_price * NEW.quantity),
                    purchase_status = 0
                WHERE inid = NEW.inid;
            END;
            '''
            db.session.execute(text(trigger_invoice_add))
            db.session.commit()

            # Trigger to update total_amount after delete
            trigger_invoice_delete = '''
            CREATE TRIGGER update_invoice_delete
            AFTER DELETE ON invoice_details
            FOR EACH ROW
            BEGIN
                UPDATE Invoice
                SET total_amount = total_amount - (OLD.unit_price * OLD.quantity)
                WHERE inid = OLD.inid;
            END;
            '''
            db.session.execute(text(trigger_invoice_delete))
            db.session.commit()

            trigger_create_invoice_if_not_exists = '''
            CREATE TRIGGER create_invoice_if_not_exists
            AFTER INSERT ON invoice_details
            FOR EACH ROW
            WHEN (SELECT COUNT(*) FROM Invoice WHERE inid = NEW.inid) = 0
            BEGIN
                INSERT INTO Invoice (inid, username, total_amount, purchase_status, date_created)
                VALUES (NEW.inid, 'Default username', NEW.unit_price * NEW.quantity, 0, CURRENT_TIMESTAMP);
            END;
            '''

            # SQL for the trigger to delete an Invoice if no instances of the inid exist in invoice_details
            trigger_delete_invoice_if_no_details = '''
            CREATE TRIGGER delete_invoice_if_no_details
            AFTER DELETE ON invoice_details
            FOR EACH ROW
            WHEN (SELECT COUNT(*) FROM invoice_details WHERE inid = OLD.inid) = 0
            BEGIN
                DELETE FROM Invoice WHERE inid = OLD.inid;
            END;
            '''
            db.session.execute(text(trigger_create_invoice_if_not_exists))
            db.session.execute(text(trigger_delete_invoice_if_no_details))

            trigger_update_quantity = '''
            -- Trigger to sum the quantity if the same product is added to the same invoice
            
                CREATE TRIGGER update_quantity_if_exists
                BEFORE INSERT ON invoice_details
                FOR EACH ROW
                WHEN EXISTS (SELECT 1 FROM invoice_details WHERE inid = NEW.inid AND pid = NEW.pid)
                BEGIN
                    UPDATE invoice_details
                    SET quantity = quantity + NEW.quantity
                    WHERE inid = NEW.inid AND pid = NEW.pid;
                END;

            '''
            
            db.session.execute(text(trigger_update_quantity))
            # db.session.execute(text(trigger_add_new))
            db.session.commit()

        # Handle NA values and load data from CSV
        print(db.session.query(Product).count())
        try:
            print("Inserting data from CSV...")
            data_path = 'websites/static/product_data.csv'
            engine = create_engine(f'sqlite:///{DB_NAME}')
            df = pd.read_csv(data_path, sep=';')

            products = []
            for idx, row in df.iterrows():
                product_data = {
                    'pid': row['ID'],
                    'title': row['TITLE'],
                    'author': row['AUTHORS'],
                    'description': row['DESCRIPTION'],
                    'price':row['PRICE'],
                    # 'date_created': func.now(),
                    'quantity': row['STOCK_KEEPING_UNIT']
                }
                products.append(product_data)
            
            # Bulk insert mappings
            db.session.bulk_insert_mappings(Product, products)
            db.session.commit()
            # Handle NA values and load data from CSV
            print(db.session.query(Invoice_Details).count())
            
        except IntegrityError as e:
            print(f"IntegrityError: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        # See tables
        print(inspect(db.engine).get_table_names())
            
    return app


