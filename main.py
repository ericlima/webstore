from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask import g
from sqlalchemy.orm import joinedload
from uuid import uuid4
from flask_mail import Mail, Message

import os
import base64

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "store.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.before_request
def load_cart_info():
    session_id, _ = get_or_create_session_id()
    items = CartItem.query.filter_by(session_id=session_id).all()
    g.cart_quantity = sum(item.quantity for item in items)
    g.cart_total = sum(item.quantity * item.product.price for item in items)

def encode_image_base64(filepath):
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    postal_code = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    items = db.relationship("OrderItem", backref="order", cascade="all, delete")

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship("Product")

# Modelos
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    artist = db.Column(db.String, nullable=False) 
    description = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String, nullable=False)
    image_base64 = db.Column(db.Text, nullable=True)
    hidden = db.Column(db.Boolean, default=False)
    reserved = db.Column(db.Boolean, default=False)             

 
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
    products = Product.query.filter_by(hidden=False).all()
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

@app.route("/manage_products", methods=["GET", "POST"])
def manage_products():
    products = Product.query.all()
    return render_template("manage_products.html", products=products)

@app.route("/toggle_product_state", methods=["POST"])
def toggle_product_state():
    product_id = request.form["product_id"]
    action = request.form["action"]

    product = Product.query.get(product_id)

    if product:
        if action == "toggle_hidden":
            product.hidden = not product.hidden
        elif action == "toggle_reserved":
            product.reserved = not product.reserved
        elif action == "delete":
            db.session.delete(product)
        db.session.commit()

    return redirect(url_for("manage_products"))

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = request.form.get("price", type=float)
        artist = request.form["artist"]

        image_file = request.files["image"]
        if image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            new_product = Product(
                name=name,
                description=description,
                price=price,
                artist=artist,
                image_url="",  # Pode ser usado no futuro se quiser armazenar caminhos
                image_base64=image_base64
            )
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for("manage_products"))

    return render_template("add_product.html")

@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form["name"]
        product.description = request.form["description"]
        product.price = request.form.get("price", type=float)
        product.artist = request.form["artist"]
        db.session.commit()
        return redirect(url_for("manage_products"))
    return render_template("edit_product.html", product=product)


# Configurar e-mail (exemplo com Gmail SMTP)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='seu.email@gmail.com',  # substitua
    MAIL_PASSWORD='sua_senha',           # substitua
)

mail = Mail(app)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    session_id, _ = get_or_create_session_id()
    cart_items = CartItem.query.options(joinedload(CartItem.product)).filter_by(session_id=session_id).all()

    if not cart_items:
        return redirect(url_for("view_cart"))

    if request.method == "POST":
        # Criar o pedido
        order = Order(
            name=request.form["name"],
            address=request.form["address"],
            postal_code=request.form["postal_code"],
            city=request.form["city"],
            phone=request.form["phone"],
            notes=request.form["notes"]
        )
        db.session.add(order)
        db.session.flush()  # para pegar o order.id

        # Adicionar itens ao pedido e reservar produtos
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.session.add(order_item)

            # Reservar produto
            product = item.product
            product.reserved = True

        # Montar corpo do e-mail
        msg = Message(
            subject="Novo Pedido Recebido",
            recipients=["angela@gmail.com"],
            body=f"""
            Novo pedido de {order.name}
            Morada: {order.address}
            Código Postal: {order.postal_code}
            Cidade: {order.city}
            Telefone: {order.phone}

            Observações:
            {order.notes or 'Nenhuma'}

            Itens:
            """ + "\n".join(f"{item.quantity}x {item.product.name}" for item in cart_items)
        )
        mail.send(msg)

        # Apagar carrinho
        CartItem.query.filter_by(session_id=session_id).delete()
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("checkout.html")

if __name__ == "__main__":
    app.run(debug=True)
