from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from uuid import uuid4
import os

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "store.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Modelos
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String, nullable=False)

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)

class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    product = db.relationship("Product")

class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

# Função de sessão
def get_or_create_session_id():
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())
        resp = make_response()
        resp.set_cookie("session_id", session_id, httponly=True)
        return session_id, resp
    return session_id, None

# Rotas
@app.route("/")
def home():
    products = Product.query.all()
    return render_template("index.html", products=products)

@app.route("/cart")
def view_cart():
    session_id, _ = get_or_create_session_id()
    cart_items = CartItem.query.options(joinedload(CartItem.product)).filter_by(session_id=session_id).all()
    return render_template("cart.html", cart_items=cart_items)

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    product_id = request.form.get("product_id", type=int)
    session_id, resp = get_or_create_session_id()

    item = CartItem.query.filter_by(session_id=session_id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = CartItem(session_id=session_id, product_id=product_id, quantity=1)
        db.session.add(item)
    db.session.commit()

    r = redirect(url_for("view_cart"))
    return resp or r

@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    product_id = request.form.get("product_id", type=int)
    session_id, _ = get_or_create_session_id()

    item = CartItem.query.filter_by(session_id=session_id, product_id=product_id).first()
    if item:
        if item.quantity > 1:
            item.quantity -= 1
        else:
            db.session.delete(item)
        db.session.commit()
    return redirect(url_for("view_cart"))

@app.route("/clear_cart", methods=["POST"])
def clear_cart():
    session_id, _ = get_or_create_session_id()
    CartItem.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    return redirect(url_for("view_cart"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        customer = Customer(
            name=request.form["name"],
            address=request.form["address"],
            phone=request.form["phone"],
            email=request.form["email"]
        )
        db.session.add(customer)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/populate")
def populate():
    if Product.query.count() == 0:
        products = [
            Product(name="Notebook Dell", description="Notebook 15'' 8GB RAM", price=3500.00, image_url="https://via.placeholder.com/300x200?text=Notebook"),
            Product(name="Smartphone Samsung", description="Galaxy S21 128GB", price=2500.00, image_url="https://via.placeholder.com/300x200?text=Smartphone"),
            Product(name="Fone Bluetooth", description="Fone sem fio com case", price=200.00, image_url="https://via.placeholder.com/300x200?text=Fone+Bluetooth"),
            Product(name="Monitor LG", description="Monitor 24'' Full HD", price=900.00, image_url="https://via.placeholder.com/300x200?text=Monitor"),
            Product(name="Teclado Mecânico", description="Teclado RGB ABNT2", price=350.00, image_url="https://via.placeholder.com/300x200?text=Teclado"),
            Product(name="Mouse Gamer", description="Mouse 7200dpi RGB", price=180.00, image_url="https://via.placeholder.com/300x200?text=Mouse"),
        ]
        db.session.add_all(products)
        db.session.commit()
    return {"message": "Produtos de exemplo inseridos."}

if __name__ == "__main__":
    app.run(debug=True)
