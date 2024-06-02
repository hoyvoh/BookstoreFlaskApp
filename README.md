# << Assignment 6 >>

* This is a basic flask application that made use of Python, Flask and SQLite to create a basic route for an e-commerce website. *

Check this demo video: [Demo](https://drive.google.com/file/d/1AUQM78yfnT8Ih7AVW6CBpm4oiD7gF0rf/view?usp=sharing)

## This basic flask app aims to:
- Load product info to models from a csv file
- Display them as a catalog
- Provide a form to insert a new product
- Can add product to cart
- Can Purchase products
- Purchased products are listed in /invoices and can view elements of a invoice in /invoice-details

#### Implemented views:
- catalog
- product details
- cart
- invoice list
- invoice details

#### Implemented models:
- product (pid, title, price, author, description)
- invoice (inid, userid, total_amount, purchase status, date)
- invoice details (inid, pid, unit_price, quantity)

## Installation and Kick start tutorial

* Windows env only, please check by yourself if you use different environment *

### Step 1: Clone the repo

```
git clone https://github.com/hoyvoh/BookstoreFlaskApp.git
```

### Step 2: Run venv and install dependencies

```
python -m venv env
./env/Scripts/activate
pip install -r requirements.txt
```

### Step 3: Run the app demo

```
python app.py
```
