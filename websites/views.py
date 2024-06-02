from flask import Blueprint, flash, jsonify,render_template, request, url_for, redirect
from . import db, DB_NAME
from .model import Product, Invoice, Invoice_Details
import logging
from sqlalchemy.sql import func
from sqlalchemy import create_engine
import random
import datetime

engine = create_engine('sqlite:///' + DB_NAME)
views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def category():
    page = int(request.args.get('page', 1))
    limit = 40
    offset = (page - 1) * limit
    
    # Query products with pagination
    products = Product.query.offset(offset).limit(limit).all()
    # Convert the products to a list of dictionaries
    product_list = []
    for product in products:
        print(product.price)
        product_dict = {
            'pid': product.pid,
            'title': product.title,
            'price': product.price,
            'author': product.author,
            'description': product.description,
            'date_created': product.date_created,
            'quantity': product.quantity
        }
        product_list.append(product_dict)
    
    print(type(product_list[0]))
    return render_template('catalog.html', products=product_list, page=page)

@views.route('/product-details', methods=['GET', 'POST'])
def product_details():
    pid = request.args.get('product_id')
    logging.debug(f'Received product_id: {pid}')
    
    if not pid:
        return "Product ID not provided", 400
    
    product = Product.query.filter_by(pid=pid).first()
    
    if product is None:
        logging.debug(f'Product with pid {pid} not found.')
        return "Product not found", 404
    
    product_dict = {
        'pid': product.pid,
        'title': product.title,
        'price': product.price,
        'author': product.author,
        'description': product.description,
        'date_created': product.date_created,
        'quantity': product.quantity
    }
    
    logging.debug(f'Found product: {product_dict}')
    
    return render_template('product_details.html', product=product_dict)

@views.route('/add-product', methods=['POST'])
def add_product():
    pid = random.randint(1, 999)
    title = request.form.get('title')
    author = request.form.get('author')
    price = request.form.get('price')
    quantity = request.form.get('quantity')
    description = request.form.get('description')
    date_created = func.now()
    
    if not title or not author or not description or len(title) < 5 or len(author) < 5 or len(description) < 5:
        flash('All fields must be at least 5 characters long.', 'error')
        return redirect(url_for('views.category'))
    
    try:
        price = float(price)
        if price <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('Price must be a number greater than 0.', 'error')
        return redirect(url_for('views.category'))
    
    if not quantity or int(quantity) < 0:
        quantity = 0
    
    new_product = Product(pid=pid, title=title, author=author, price=price, quantity=quantity, description=description, date_created=date_created)
    db.session.add(new_product)
    db.session.commit()
    flash('Book added successfully!', 'success')
    
    return redirect(url_for('views.category'))

@views.route('/delete-product', methods=['POST'])
def delete_product():
    pid = request.form.get('product_id')
    
    product = Product.query.filter_by(pid=pid).first()
    
    if product:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    else:
        flash('Product not found.', 'error')
    
    return redirect(url_for('views.category'))

@views.route('/modify-product', methods=['POST'])
def modify_products():
    flash('product data modified')
    return jsonify({})

@views.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    pid = request.form.get('product_id')
    if not pid:
        flash('Product ID is required to add to cart.', 'error')
        return redirect(url_for('views.category'))

    # Assuming you have a Cart model and a function to add items to the cart
    product = Product.query.filter_by(pid=pid).first()
    print(product.pid)
    if product:
        # Check if the product is already in the cart
        existing_item = Invoice_Details.query.filter_by(pid=pid).first()
        if existing_item:
            # Update the quantity of the existing item
            existing_item.quantity += 1
            flash(f'Added one more {product.title} to cart.', 'success')
        else:
            # Add the product to the cart
            inid = 1  # Assuming inid is 1 for now
            unit_price = product.price
            quantity = 1  # Assuming initial quantity is 1
            new_invoice_item = Invoice_Details(inid=inid, pid=pid, unit_price=unit_price, quantity=quantity)
            db.session.add(new_invoice_item)
            flash(f'Added {product.title} to cart.', 'success')
        
        db.session.commit()
    else:
        flash('Product not found.', 'error')
    
    return redirect(url_for('views.category'))


@views.route('/cart', methods=['GET', 'POST'])
def cart():
    # Get the list of items in the cart
    cart_items = db.session.query(Invoice_Details)\
        .join(Invoice, Invoice_Details.inid == Invoice.inid)\
        .filter(Invoice.purchase_status == False)\
        .all()
    
    if request.method == 'POST':
        selected_products = request.form.getlist('product')
        
        # Calculate the total amount of the selected products
        total_amount = 0
        for product_id in selected_products:
            product_id = int(product_id)
            product = Product.query.get(product_id)
            quant = db.session.query(Invoice_Details)\
                .join(Invoice, Invoice_Details.inid == Invoice.inid)\
                .filter(Invoice.purchase_status == False)\
                .filter(Invoice_Details.pid == product_id)\
                .first()
            print(quant)
            if product:
                total_amount += product.price * quant.quantity  # Multiply by quantity

        # Deduct the total amount from the existing invoice with inid=1
        existing_invoice = Invoice.query.filter_by(inid=1).first()
        if existing_invoice:
            existing_invoice.total_amount -= total_amount

        # Create a new invoice for the purchase
        new_invoice = Invoice(username='Default username', total_amount=total_amount, purchase_status=True)
        db.session.add(new_invoice)
        db.session.flush()  # Flush to get the auto-generated inid

        new_inid = new_invoice.inid
        print(new_inid)

        # Update the inid for the selected products in Invoice_Details table
        for product_id in selected_products:
            product_id = int(product_id)
            # Update the Invoice_Details table
            invoice_detail = Invoice_Details.query.filter_by(pid=product_id).first()
            invoice_detail.inid = new_inid

        db.session.commit()
        flash('Purchase successful.', 'success')
        return redirect(url_for('views.cart'))

    
    return render_template('cart.html', cart_items=cart_items)



@views.route('/invoices', methods=['GET', 'POST'])
def invoices():
    invoices = db.session.query(Invoice).filter(Invoice.purchase_status==True).all()
    for invoice in invoices:
        print(invoice.inid)

    return render_template("invoice.html", invoices=invoices)

@views.route('/invoice-details', methods=['GET', 'POST'])
def invoice_details():
    invoice = db.session.query(Invoice).filter(Invoice.inid==request.args.get('invoice_id', 1)).all()
    products = db.session.query(Invoice_Details).filter(Invoice_Details.inid==request.args.get('invoice_id', 1)).all()
    return render_template("invoice_details.html", invoice=invoice, products=products)