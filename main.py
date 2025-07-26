from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.orm import joinedload
from uuid import uuid4

import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'store.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Modelos
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String, nullable=False)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    product = relationship("Product")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    subject = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)    

Base.metadata.create_all(bind=engine)

# Rotas principais
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "products": products})

def get_or_create_session_id(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())
        response.set_cookie(key="session_id", value=session_id, httponly=True)
    return session_id

@app.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request):
    db = SessionLocal()    
    cart_items = db.query(CartItem).options(joinedload(CartItem.product)).all()
    db.close()
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items})

@app.post("/add_to_cart")
def add_to_cart(request: Request, response: Response, product_id: int = Form(...)):
    db = SessionLocal()
    session_id = get_or_create_session_id(request, response)

    item = db.query(CartItem).filter_by(session_id=session_id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = CartItem(session_id=session_id, product_id=product_id, quantity=1)
        db.add(item)
    db.commit()
    db.close()
    return RedirectResponse(url="/cart", status_code=303)


@app.post("/remove_from_cart")
def remove_from_cart(request: Request, response: Response, product_id: int = Form(...)):
    db = SessionLocal()
    session_id = get_or_create_session_id(request, response)

    item = db.query(CartItem).filter_by(session_id=session_id, product_id=product_id).first()
    if item:
        if item.quantity > 1:
            item.quantity -= 1
        else:
            db.delete(item)
    db.commit()
    db.close()
    return RedirectResponse(url="/cart", status_code=303)


@app.post("/clear_cart")
def clear_cart(request: Request, response: Response):
    db = SessionLocal()
    session_id = get_or_create_session_id(request, response)

    db.query(CartItem).filter_by(session_id=session_id).delete()
    db.commit()
    db.close()
    return RedirectResponse(url="/cart", status_code=303)



@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_customer(name: str = Form(...), address: str = Form(...), phone: str = Form(...), email: str = Form(...)):
    db = SessionLocal()
    customer = Customer(name=name, address=address, phone=phone, email=email)
    db.add(customer)
    db.commit()
    db.close()
    return RedirectResponse(url="/", status_code=303)

@app.get("/populate")
def populate():
    db = SessionLocal()
    if db.query(Product).count() == 0:
        products = [
            Product(name="Notebook Dell", description="Notebook 15'' 8GB RAM", price=3500.00, image_url="https://via.placeholder.com/300x200?text=Notebook"),
            Product(name="Smartphone Samsung", description="Galaxy S21 128GB", price=2500.00, image_url="https://via.placeholder.com/300x200?text=Smartphone"),
            Product(name="Fone Bluetooth", description="Fone sem fio com case", price=200.00, image_url="https://via.placeholder.com/300x200?text=Fone+Bluetooth"),
            Product(name="Monitor LG", description="Monitor 24'' Full HD", price=900.00, image_url="https://via.placeholder.com/300x200?text=Monitor"),
            Product(name="Teclado Mecânico", description="Teclado RGB ABNT2", price=350.00, image_url="https://via.placeholder.com/300x200?text=Teclado"),
            Product(name="Mouse Gamer", description="Mouse 7200dpi RGB", price=180.00, image_url="https://via.placeholder.com/300x200?text=Mouse"),
        ]
        db.add_all(products)
        db.commit()
    db.close()
    return {"message": "Produtos de exemplo inseridos."} 