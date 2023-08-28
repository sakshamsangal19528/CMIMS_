from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
from datetime import datetime
import pdfkit
import plotly.graph_objs as go
from plotly.subplots import make_subplots

current_directory = os.path.dirname(os.path.abspath(__file__))
wkhtmltopdf_path = os.path.join(current_directory, 'wkhtmltopdf', 'bin', 'wkhtmltopdf.exe')
pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
# pdfkit_config = pdfkit.configuration(wkhtmltopdf='C:/Users/saksh/Desktop/flask project
# 3/wkhtmltopdf/bin/wkhtmltopdf.exe')

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'mydatabase.db')
db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(255), nullable=False)
    product = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.String(255), nullable=False)
    date_updated = db.Column(db.String(255), nullable=True)


class Product_history(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(255), nullable=False)
    product = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.String(255), nullable=False)
    date_updated = db.Column(db.String(255), nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False, default='regular')


class SoldItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_total = db.Column(db.Float, nullable=False)
    date_sold = db.Column(db.String(255), nullable=False)
    buyer_name = db.Column(db.String(255), nullable=False)
    bill_id = db.Column(db.String(255), nullable=False)


def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get('user_id'):
            user = User.query.get(session['user_id'])
            if user.user_type == 'admin':
                return func(*args, **kwargs)
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('dashboard'))
    return decorated_function


def unique_bill_id():
    unique_id = secrets.token_hex(4).upper()
    date_time = datetime.now().strftime("%Y%m%d%H%M%S")
    return unique_id+date_time


def update_product_history(product_id, new_product_id, new_product_name, new_quantity,
                           new_price, new_location, new_date_added, new_date_updated):
    existing_product_history = Product_history.query.filter_by(product_id=product_id).first()

    if existing_product_history:
        existing_product_history.product_id = new_product_id
        existing_product_history.product = new_product_name
        existing_product_history.quantity = new_quantity
        existing_product_history.price = new_price
        existing_product_history.location = new_location
        existing_product_history.date_added = new_date_added
        existing_product_history.date_updated = new_date_updated
        db.session.commit()


@app.route("/")
def home():
    return render_template("home.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            user_type = request.form['user_type']

            # Perform password validation
            if len(password) < 8:
                flash("Password must be at least 8 characters long.", "error")
                return render_template('register.html')
            if ' ' in password:
                flash("Password cannot contain spaces.", "error")
                return render_template('register.html')

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password, user_type=user_type)
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")
            print(str(e))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                if user.user_type == 'admin':
                    return redirect(url_for('profile'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password.", "error")
        except Exception as e:
            flash("Login failed. Please try again.", "error")
            print(str(e))
    return render_template('login.html')


@app.route("/my_website")
def my_website():
    return render_template("my_website.html")


@app.route("/profile", methods=['GET', 'POST'])
@admin_required
def profile():
    if request.method == 'POST':
        try:
            product_id = request.form['product_id'].upper()
            product = request.form['product']
            quantity = request.form['quantity']
            price = request.form['price']
            location = request.form['location']
            date_added = datetime.now().strftime("%Y-%m-%d")
            date_updated = "N/A"

            existing_product = Product.query.filter_by(product_id=product_id).first()
            if existing_product:
                flash("A product with this ID already exists.", "error")
            else:
                new_product = Product(product_id=product_id,
                                      product=product,
                                      quantity=quantity,
                                      price=price,
                                      location=location,
                                      date_added=date_added,
                                      date_updated=date_updated)

                all_products = Product_history(product_id=product_id,
                                               product=product,
                                               quantity=quantity,
                                               price=price,
                                               location=location,
                                               date_added=date_added,
                                               date_updated=date_updated)
                db.session.add(new_product)
                db.session.add(all_products)
                db.session.commit()
                flash("Product added successfully.", "success")

        except Exception as e:
            db.session.rollback()
            flash("Failed to add product. Please try again.", "error")
            print(str(e))
    product_items = Product.query.all()
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            return render_template("profile.html", username=user.username, product_items=product_items)
    flash("You are not logged in. Please log in to access your profile.", "error")
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:

            # Calculate statistics for colored boxes
            total_products_count_2 = Product.query.count()
            low_stock_products_2 = Product.query.filter(Product.quantity <= 10).count()

            most_stock_product_2 = Product.query.order_by(Product.quantity.desc()).first()
            least_stock_product_2 = Product.query.order_by(Product.quantity).first()
            out_of_stock_products_2 = Product.query.filter(Product.quantity == 0).count()

            # Calculate statistics
            total_products = Product.query.all()  # Get all products
            low_stock_products = Product.query.filter(Product.quantity <= 10).all()  # Get low stock products

            most_stock_product = Product.query.order_by(Product.quantity.desc()).first()
            least_stock_product = Product.query.order_by(Product.quantity).first()

            out_of_stock_products = Product.query.filter(Product.quantity == 0).all()  # Get out of stock products

            return render_template("dashboard.html", username=user.username,
                                   total_products_2=total_products_count_2,
                                   low_stock_products_2=low_stock_products_2,
                                   most_stock_product_2=most_stock_product_2,
                                   least_stock_product_2=least_stock_product_2,
                                   out_of_stock_products_2=out_of_stock_products_2,

                                   total_products=total_products,
                                   low_stock_products=low_stock_products,
                                   most_stock_product=most_stock_product,
                                   least_stock_product=least_stock_product,
                                   out_of_stock_products=out_of_stock_products
                                   )
    flash("You are not logged in. Please log in to access your profile.", "error")
    return redirect(url_for('login'))


@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            new_product_id = request.form['product_id'].upper()
            new_product_name = request.form['product']
            new_quantity = request.form['quantity']
            new_price = request.form['price']
            new_location = request.form['location']
            new_date_updated = datetime.now().strftime("%Y-%m-%d")

            existing_product = Product.query.filter(Product.product_id == new_product_id,
                                                    Product.id != product.id).first()
            if existing_product:
                flash("A product with this ID already exists.", "error")
            else:
                product.product_id = new_product_id.upper()
                product.product = new_product_name
                product.quantity = new_quantity
                product.price = new_price
                product.location = new_location
                product.date_updated = new_date_updated
                db.session.commit()

                # Update the product history
                update_product_history(product.product_id, new_product_id, new_product_name,
                                       new_quantity, new_price, new_location, product.date_added, new_date_updated)

                flash('Product updated successfully.', 'success')
                return redirect(url_for('profile'))

        except Exception as e:
            db.session.rollback()
            flash("Failed to update product. Please try again.", "error")
            print(str(e))
    return render_template('edit_product.html', product=product)


@app.route('/delete/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('delete_product.html', product=product)


@app.route('/products', methods=['GET'])
def products():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            all_products = Product.query.all()
            return render_template("products.html", username=user.username, products=all_products)
    flash("You are not logged in. Please log in to access your profile.", "error")
    return redirect(url_for('login'))


@app.route('/products_history', methods=['GET'])
def products_history():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            all_products = Product_history.query.all()
            return render_template("products_history.html", username=user.username, products=all_products)
    flash("You are not logged in. Please log in to access your profile.", "error")
    return redirect(url_for('login'))


@app.route('/cashier', methods=['GET', 'POST'])
def cashier():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            if request.method == 'POST':
                product_id = request.form['product_id']
                quantity_sold = int(request.form['quantity_sold'])
                buyer_name = request.form['buyer_name']  # get the buyers name from here

                product = Product.query.filter_by(product_id=product_id).first()
                if product:
                    if product.quantity >= quantity_sold:
                        product.quantity -= quantity_sold
                        db.session.commit()

                        # Add to SoldItem with buyer's name
                        sold_item = SoldItem(
                            product_id=product.product_id,
                            product_name=product.product,
                            quantity_sold=quantity_sold,
                            price=product.price,
                            order_total=product.price * quantity_sold,
                            date_sold=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            buyer_name=buyer_name,  # Added buyer's name here for table
                            bill_id=unique_bill_id()
                        )
                        db.session.add(sold_item)
                        db.session.commit()

                        flash(f"Sold {quantity_sold} {product.product}(s) to {buyer_name} successfully.", "success")
                    else:
                        flash("Not enough quantity available to sell.", "error")
                else:
                    flash("Product not found.", "error")

            all_products = Product.query.all()
            return render_template("cashier.html", username=user.username, products=all_products)
    flash("You are not logged in. Please log in to access your profile.", "error")
    return redirect(url_for('login'))


@app.route('/sell_history')
def sell_history():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            sold_items = SoldItem.query.all()  # Fetch all the sold items from the database
            return render_template("sell_history.html", username=user.username, sold_items=sold_items)
    flash("You are not logged in. Please log in to access your profile.", "error")
    return redirect(url_for('login'))


@app.route('/generate_bill/<string:bill_id>', methods=['POST'])
def generate_bill(bill_id):
    sold_item = SoldItem.query.filter_by(bill_id=bill_id).first()
    if sold_item:
        # Calculate GST and total price including GST
        gst_amount = sold_item.order_total * 0.18
        total_price_with_gst = sold_item.order_total + gst_amount

        # Convert the calculated values to string format for template rendering
        gst_amount_str = "₹ {:.2f}".format(gst_amount)
        total_price_with_gst_str = "₹ {:.2f} /-".format(total_price_with_gst)

        # Add the calculated values to the sold_item object
        sold_item.gst_amount = gst_amount_str
        sold_item.total_price_with_gst = total_price_with_gst_str

        rendered = render_template('bill.html', sold_item=sold_item)
        return rendered
    else:
        flash("Sold item not found.", "error")
        return redirect(url_for('sell_history'))


@app.route('/pdf_bill/<string:bill_id>', methods=['GET'])
def pdf_bill(bill_id):
    sold_item = SoldItem.query.filter_by(bill_id=bill_id).first()
    if sold_item:
        rendered = render_template('bill.html', sold_item=sold_item)
        pdf = pdfkit.from_string(rendered, False)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=bill_{bill_id}.pdf'

        return response
    else:
        flash("Sold item not found.", "error")
        return redirect(url_for('sell_history'))


@app.route('/balance_report')
def balance_report():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            sold_items = SoldItem.query.all()

            # Extract data for the graph
            product_names = [item.product_name for item in sold_items]
            quantities_sold = [item.quantity_sold for item in sold_items]
            dates_sold = [item.date_sold for item in sold_items]

            # Create a scatter plot with quantity on the y-axis and date on the x-axis
            scatter_trace = go.Scatter(x=dates_sold, y=quantities_sold, mode='markers+text', text=product_names,
                                       marker=dict(color='blue'))

            # Create a subplot with the scatter plot
            fig = make_subplots(rows=1, cols=1, subplot_titles=("Product Sales Report",))
            fig.add_trace(scatter_trace, row=1, col=1)

            # Update layout
            fig.update_layout(showlegend=False, height=500)
            fig.update_layout(scene=dict(xaxis_title="Date Sold", yaxis_title="Quantity Sold"))

            # Convert to HTML and pass to the template
            graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

            return render_template("balance_report.html", username=user.username, graph_html=graph_html)
    flash("You are not logged in. Please log in to access your profile.", "error")
    return redirect(url_for('login'))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully.", "success")
    return redirect("/login")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
