# imports - standard imports
import os
import json
import sqlite3
import pandas as pd

# imports - third party imports
from flask import Flask,Response, url_for, request, redirect,jsonify
from flask import render_template as render
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

# global constants
DATABASE_NAME = 'inventory.sqlite'

# setting up Flask instance
app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'database', DATABASE_NAME),
)

# listing views
link = {x: x for x in ["location", "product","search","upload"]}
link["index"] = '/'


def init_database():
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    # initialize page content
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(Material INTEGER PRIMARY KEY,
                    Material_Description TEXT,
                    MTyp TEXT,
                    Typ TEXT,
                    Division TEXT,
                    ABC TEXT,
                    Reorder_Pt TEXT,
                    Max_Level TEXT,
                    Total_Stock TEXT,
                    loc_name TEXT);
    """)

    # # initialize page content
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS products(prod_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                 prod_name TEXT UNIQUE NOT NULL,
    #                 prod_quantity INTEGER NOT NULL,
    #                 loc_name Text NOT NULL);
    # """)

    # initialize page content
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS location(loc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 loc_name TEXT UNIQUE NOT NULL);
    """)
    db.commit()


@app.route('/search',methods=['GET','POST'])
def inventory():
    init_database()
    msg = None
    products = None
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()
    if request.method == 'POST':
        search = request.form['Material_id']
        try:
            querry="SELECT * FROM products WHERE Material LIKE '{}%' ORDER BY Material".format(search)
            cursor.execute(querry)
            products = cursor.fetchall()
        except sqlite3.Error as e:
            msg = f"An error occurred: {e.args[0]}"
        if msg:
            print(msg)
        return render('search.html',form=search,link=link, title="inventory",  products=products)
    return render('search.html',link=link, title="Search History",  products=products)

@app.route('/',methods=['GET','POST'])
def summary():
    init_database()
    msg = None
    warehouse, products = None, None
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM location")  # <---------------------------------FIX THIS
        warehouse = cursor.fetchall()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
    except sqlite3.Error as e:
        msg = f"An error occurred: {e.args[0]}"
    if msg:
        print(msg)

    return render('index.html', link=link, title="Summary", warehouses=warehouse, products=products)


@app.route('/product', methods=['POST', 'GET'])
def product():
    init_database()
    msg = None
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    if request.method == 'POST':
        Material_id = request.form['Material']
        Material_Description = request.form['Material_Description']
        MTyp = request.form['MTyp']
        Typ = request.form['Typ']
        Division = request.form['Division']
        ABC = request.form['ABC']
        Reorder_Pt = request.form['Reorder_Pt']
        Max_Level = request.form['Max_Level']
        Total_Stock = request.form['Total_Stock']
        location = request.form['loc_name']
        if True:
            try:
                cursor.execute("SELECT * FROM location WHERE loc_name=?", (location,))
                rs = cursor.fetchone()
                if rs==None:
                    try:
                        cursor.execute("INSERT INTO location (loc_name) VALUES (?)", (location,))
                        db.commit()
                    except sqlite3.Error as e:
                        msg = f"An error occurred: {e.args[0]}"
                    if msg:
                        print(msg)   
                cursor.execute("INSERT INTO products (Material, Material_Description, MTyp,Typ,Division,ABC,Reorder_Pt,Max_Level,Total_Stock,loc_name) VALUES (?, ?, ?,?,?, ?, ?,?,?,?,?)", (Material_id, Material_Description,MTyp,Typ,Division,ABC,Reorder_Pt,Max_Level,Total_Stock,location,))
                db.commit()
            except sqlite3.Error as e:
                msg = f"An error occurred: {e.args[0]}"
            else:
                msg = f"{Material_id} added successfully"

            if msg:
                print(msg)

            return redirect(url_for('product'))

    return render('product.html',
                  link=link, products=products, transaction_message=msg,
                  title="Products")


@app.route('/upload', methods=['POST', 'GET'])
def product_upload():
    init_database()
    msg = None
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    if request.method == 'POST':
            try:
               if request.files:
                    # On upload I am Dropping Table and Recreating new one to remove duplicates
                    cursor.execute("""
                    DROP TABLE IF EXISTS products
                    """)
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products(Material INTEGER PRIMARY KEY,
                                    Material_Description TEXT,
                                    MTyp TEXT,
                                    Typ TEXT,
                                    Division TEXT,
                                    ABC TEXT,
                                    Reorder_Pt TEXT,
                                    Max_Level TEXT,
                                    Total_Stock TEXT,
                                    loc_name TEXT);
                    """)
                    file = request.files["filename"]
                    file.save(os.path.join(ROOT_PATH,file.filename))
                    df = pd.read_excel(os.path.join(ROOT_PATH,file.filename))
                    df.to_sql('products', con=db, if_exists='append', index=False, chunksize=100)
                    try: 
                        os.remove(os.path.join(ROOT_PATH,file.filename)) 
                        print("% s removed successfully" % os.path.join(ROOT_PATH,file.filename)) 
                    except OSError as error: 
                        print(error) 
                        print("File path can not be removed") 

                    cursor.execute("SELECT * FROM products")
                    products = cursor.fetchall()
                    return render('upload.html',link=link, products=products,title="Inventory Summary")
            except Exception as e:
                 msg = f"An error occurred: {e}"
            if msg:
                print(msg)     

    return render('upload.html',
                  link=link, products=products, transaction_message=msg,
                  title="Product Inventory")

@app.route('/location', methods=['POST', 'GET'])
def location():
    init_database()
    msg = None
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    cursor.execute("SELECT * FROM location")
    warehouse_data = cursor.fetchall()

    if request.method == 'POST':
        warehouse_name = request.form['warehouse_name']

        transaction_allowed = False
        if warehouse_name not in ['', ' ', None]:
            transaction_allowed = True

        if transaction_allowed:
            try:
                cursor.execute("INSERT INTO location (loc_name) VALUES (?)", (warehouse_name,))
                db.commit()
            except sqlite3.Error as e:
                msg = f"An error occurred: {e.args[0]}"
            else:
                msg = f"{warehouse_name} added successfully"

            if msg:
                print(msg)

            return redirect(url_for('location'))

    return render('location.html',
                  link=link, warehouses=warehouse_data, transaction_message=msg,
                  title="Warehouse Locations")


@app.route('/delete')
def delete():
    type_ = request.args.get('type')
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    if type_ == 'location':
        id_ = request.args.get('loc_id')
        cursor.execute("DELETE FROM location WHERE loc_id == ?", [str(id_)])
        db.commit()
        return redirect(url_for('location'))

    elif type_ == 'product':
        id_ = request.args.get('prod_id')
        print(id_)
        cursor.execute("DELETE FROM products WHERE Material == ?", [str(id_)])
        db.commit()

        return redirect(url_for('product'))

@app.route('/deleteAll')
def deleteAll():
    type_ = request.args.get('type')
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    if type_ == 'location':
        cursor.execute("DROP TABLE location")
        db.commit()
        return redirect(url_for('location'))

    elif type_ == 'product':
        cursor.execute("DROP TABLE products")
        db.commit()

        return redirect(url_for('product'))        


@app.route('/edit', methods=['POST', 'GET'])
def edit():
    type_ = request.args.get('type')
    db = sqlite3.connect(DATABASE_NAME)
    cursor = db.cursor()

    if type_ == 'location' and request.method == 'POST':
        loc_id = request.form['loc_id']
        loc_name = request.form['loc_name']

        if loc_name:
            cursor.execute("UPDATE location SET loc_name = ? WHERE loc_id == ?", (loc_name, str(loc_id)))
            db.commit()

        return redirect(url_for('location'))

    elif type_ == 'product' and request.method == 'POST':
        Material_id = request.form['Material']
        Material_Description = request.form['Material_Description']
        MTyp = request.form['MTyp']
        Typ = request.form['Typ']
        Division = request.form['Division']
        ABC = request.form['ABC']
        Reorder_Pt = request.form['Reorder_Pt']
        Max_Level = request.form['Max_Level']
        Total_Stock = request.form['Total_Stock']
        location = request.form['loc_name']
        if Material_Description:
            cursor.execute("UPDATE products SET Material_Description = ? WHERE Material == ?", (Material_Description, str(Material_id)))
        if MTyp:
            cursor.execute("UPDATE products SET MTyp = ? WHERE Material == ?", (MTyp, str(Material_id)))
        if Typ:
            cursor.execute("UPDATE products SET Typ = ? WHERE Material == ?", (Typ, str(Material_id))) 
        if Division:
            cursor.execute("UPDATE products SET Division = ? WHERE Material == ?", (Division, str(Material_id)))
        if ABC:
            cursor.execute("UPDATE products SET ABC = ? WHERE Material == ?", (ABC, str(Material_id)))
        if Reorder_Pt:
            cursor.execute("UPDATE products SET Reorder_Pt = ? WHERE Material == ?", (Reorder_Pt, str(Material_id)))
        if Max_Level:
            cursor.execute("UPDATE products SET Max_Level = ? WHERE Material == ?", (Max_Level, str(Material_id)))                            
        if Total_Stock:
            cursor.execute("UPDATE products SET Total_Stock = ?"
                           "WHERE Material == ?", (Total_Stock, str(Material_id)))
        if location:
           cursor.execute("UPDATE products SET loc_name = ? WHERE Material == ?", (location, str(Material_id)))            
        db.commit()

        return redirect(url_for('product'))

    return render(url_for(type_))
