from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-change-this'  # cámbialo si subes a prod
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    stock = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0)   # costo unitario
    price = db.Column(db.Float, default=0)  # precio unitario
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('movements', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'purchase' o 'sale'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    profit = db.Column(db.Float, default=0)  # ganancia
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    client = db.relationship('Client', backref='movements')


@app.route('/')
def index():
    return redirect(url_for('inventory'))

@app.route('/products')
def products():
    products = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=products)

@app.route('/products/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        name = request.form['name'].strip()
        sku = request.form.get('sku', '').strip()
        try:
            initial = int(request.form.get('stock', 0))
        except ValueError:
            initial = 0
        try:
            cost = float(request.form.get('cost', 0))
        except ValueError:
            cost = 0
        try:
            price = float(request.form.get('price', 0))
        except ValueError:
            price = 0
        if not name:
            flash('El nombre es requerido.', 'danger')
            return redirect(url_for('new_product'))
        if Product.query.filter_by(name=name).first():
            flash('Ya existe un producto con ese nombre.', 'danger')
            return redirect(url_for('new_product'))
        p = Product(name=name, sku=sku, stock=initial, cost=cost, price=price)
        db.session.add(p)
        db.session.commit()
        flash('Producto creado.', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Crear', product=None)


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    p = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        p.name = request.form['name'].strip()
        p.sku = request.form.get('sku', '').strip()
        try:
            p.stock = int(request.form.get('stock', p.stock))
        except ValueError:
            flash('Stock inválido', 'danger')
            return redirect(url_for('edit_product', product_id=product_id))
        try:
            p.cost = float(request.form.get('cost', 0))
        except ValueError:
            p.cost = 0
        try:
            p.price = float(request.form.get('price', 0))
        except ValueError:
            p.price = 0
        db.session.commit()
        flash('Producto actualizado', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Editar', product=p)

@app.route('/clients')
def clients():
    clients = Client.query.order_by(Client.name).all()
    return render_template('clients.html', clients=clients)

@app.route('/clients/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        if not name:
            flash('El nombre es requerido.', 'danger')
            return redirect(url_for('new_client'))

        if Client.query.filter_by(name=name).first():
            flash('Ya existe un cliente con ese nombre.', 'danger')
            return redirect(url_for('new_client'))

        c = Client(name=name, phone=phone, email=email)
        db.session.add(c)
        db.session.commit()
        flash('Cliente creado.', 'success')
        return redirect(url_for('clients'))

    return render_template('client_form.html', action='Crear', client=None)

@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    c = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        c.name = request.form['name'].strip()
        c.phone = request.form.get('phone', '').strip()
        c.email = request.form.get('email', '').strip()
        db.session.commit()
        flash('Cliente actualizado.', 'success')
        return redirect(url_for('clients'))
    return render_template('client_form.html', action='Editar', client=c)


@app.route('/inventory')
def inventory():
    products = Product.query.order_by(Product.name).all()
    return render_template('inventory.html', products=products)


@app.route('/purchase/new', methods=['GET', 'POST'])
def new_purchase():
    products = Product.query.order_by(Product.name).all()
    clients = Client.query.order_by(Client.name).all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        qty = int(request.form['quantity'])
        client_id = request.form.get('client_id')
        if qty <= 0:
            flash('La cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('new_purchase'))
        product = Product.query.get_or_404(product_id)
        product.stock += qty
        mov = Movement(product=product, quantity=qty, type='purchase',
                       profit=0, client_id=client_id if client_id else None)
        db.session.add(mov)
        db.session.commit()
        flash('Compra registrada', 'success')
        return redirect(url_for('inventory'))
    return render_template('purchase_form.html', products=products, clients=clients)


@app.route('/sale/new', methods=['GET', 'POST'])
def new_sale():
    products = Product.query.order_by(Product.name).all()
    clients = Client.query.order_by(Client.name).all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        qty = int(request.form['quantity'])
        client_id = request.form.get('client_id')
        if qty <= 0:
            flash('La cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('new_sale'))
        product = Product.query.get_or_404(product_id)
        if product.stock < qty:
            flash(f'Stock insuficiente. Stock actual: {product.stock}', 'danger')
            return redirect(url_for('new_sale'))
        product.stock -= qty
        profit = (product.price - product.cost) * qty
        mov = Movement(product=product, quantity=qty, type='sale',
                       profit=profit, client_id=client_id if client_id else None)
        db.session.add(mov)
        db.session.commit()
        flash('Venta registrada', 'success')
        return redirect(url_for('inventory'))
    return render_template('sale_form.html', products=products, clients=clients)


@app.route('/movements')
def movements():
    movements = Movement.query.order_by(Movement.timestamp.desc()).limit(200).all()
    return render_template('movements.html', movements=movements)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # crea la DB y tablas si no existen
    app.run(debug=True)

## Para iniciar la app.py utilizamos: venv\Scripts\Activate.ps1
## Luego: python app.py
