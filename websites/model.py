from . import db
from sqlalchemy.sql import func

# - product (pid, title, price, author, description, date created, quantity)
# - invoice (inid, userid, total_amount, purchase status, date)
# - invoice details (inid, pid, unit_price, quantity)

class Product(db.Model):
    __tablename__ = 'Product'
    pid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default='Book Title')
    price = db.Column(db.Integer, default=0)
    author = db.Column(db.String(100), default='Many Authors')
    description = db.Column(db.String(1000), default='No description')
    date_created = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    quantity = db.Column(db.Integer, default=0)

class Invoice(db.Model):
    __tablename__='Invoice'
    inid = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    total_amount = db.Column(db.Integer, nullable=False, default=0)
    purchase_status = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)

class Invoice_Details(db.Model):
    __tablename__='invoice_details'
    inid = db.Column(db.Integer, db.ForeignKey(Invoice.inid), primary_key=True, nullable=False)
    pid = db.Column(db.Integer, db.ForeignKey(Product.pid), primary_key=True, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False, default=0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
