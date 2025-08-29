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
    name = db.Column(db.String(120), nullable=False, unique=True)
    sku = db.Column(db.String(50), unique=True)
    stock = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('movements', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'purchase' or 'sale'
    note = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
        if not name:
            flash('El nombre es requerido.', 'danger')
            return redirect(url_for('new_product'))
        if Product.query.filter_by(name=name).first():
            flash('Ya existe un producto con ese nombre.', 'danger')
            return redirect(url_for('new_product'))
        p = Product(name=name, sku=sku, stock=initial)
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
        db.session.commit()
        flash('Producto actualizado', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Editar', product=p)

@app.route('/inventory')
def inventory():
    products = Product.query.order_by(Product.name).all()
    return render_template('inventory.html', products=products)

@app.route('/movement/new', methods=['GET', 'POST'])
def new_movement():
    products = Product.query.order_by(Product.name).all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        mtype = request.form['type']
        try:
            qty = int(request.form['quantity'])
        except ValueError:
            flash('Cantidad inválida', 'danger')
            return redirect(url_for('new_movement'))
        product = Product.query.get_or_404(product_id)
        if qty <= 0:
            flash('Cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('new_movement'))
        if mtype == 'sale' and product.stock < qty:
            flash(f'Stock insuficiente. Stock actual: {product.stock}', 'danger')
            return redirect(url_for('new_movement'))
        # aplicar cambio
        if mtype == 'purchase':
            product.stock += qty
        else:
            product.stock -= qty
        mov = Movement(product=product, quantity=qty, type=mtype)
        db.session.add(mov)
        db.session.commit()
        flash('Movimiento registrado', 'success')
        return redirect(url_for('inventory'))
    return render_template('movement_form.html', products=products)

@app.route('/purchase/new', methods=['GET', 'POST'])
def new_purchase():
    products = Product.query.order_by(Product.name).all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        qty = int(request.form['quantity'])
        if qty <= 0:
            flash('La cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('new_purchase'))
        product = Product.query.get_or_404(product_id)
        product.stock += qty
        mov = Movement(product=product, quantity=qty, type='purchase')
        db.session.add(mov)
        db.session.commit()
        flash('Compra registrada', 'success')
        return redirect(url_for('inventory'))
    return render_template('purchase_form.html', products=products)


@app.route('/sale/new', methods=['GET', 'POST'])
def new_sale():
    products = Product.query.order_by(Product.name).all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        qty = int(request.form['quantity'])
        if qty <= 0:
            flash('La cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('new_sale'))
        product = Product.query.get_or_404(product_id)
        if product.stock < qty:
            flash(f'Stock insuficiente. Stock actual: {product.stock}', 'danger')
            return redirect(url_for('new_sale'))
        product.stock -= qty
        mov = Movement(product=product, quantity=qty, type='sale')
        db.session.add(mov)
        db.session.commit()
        flash('Venta registrada', 'success')
        return redirect(url_for('inventory'))
    return render_template('sale_form.html', products=products)


@app.route('/movements')
def movements():
    movements = Movement.query.order_by(Movement.timestamp.desc()).limit(200).all()
    return render_template('movements.html', movements=movements)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # crea la DB y tablas si no existen
    app.run(debug=True)
