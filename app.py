from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)

# ==================================================
# CONFIG
# ==================================================

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

# ==================================================
# DATABASE
# ==================================================

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200))
    harga = db.Column(db.Integer)
    stok = db.Column(db.Integer)
    deskripsi = db.Column(db.Text)
    gambar = db.Column(db.String(200))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_pembeli = db.Column(db.String(200))
    alamat = db.Column(db.Text)
    total = db.Column(db.Integer)
    status = db.Column(db.String(100))
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)

# ==================================================
# HOME
# ==================================================

@app.route('/')
def index():

    products = Product.query.all()

    return render_template(
        'index.html',
        products=products
    )

# ==================================================
# DETAIL PRODUK
# ==================================================

@app.route('/product/<int:id>')
def product_detail(id):

    product = Product.query.get_or_404(id)

    return render_template(
        'detail.html',
        product=product
    )

# ==================================================
# ADD TO CART
# ==================================================

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):

    product = Product.query.get_or_404(id)

    if 'cart' not in session:
        session['cart'] = []

    item = {
        'id': product.id,
        'nama': product.nama,
        'harga': product.harga,
        'gambar': product.gambar
    }

    session['cart'].append(item)

    session.modified = True

    flash('Produk berhasil ditambahkan ke keranjang!', 'success')

    return redirect(url_for('cart'))

# ==================================================
# CART
# ==================================================

@app.route('/cart')
def cart():

    cart = session.get('cart', [])

    total = sum(item['harga'] for item in cart)

    return render_template(
        'cart.html',
        cart=cart,
        total=total
    )

# ==================================================
# REMOVE CART
# ==================================================

@app.route('/remove_cart/<int:index>')
def remove_cart(index):

    cart = session.get('cart', [])

    if len(cart) > index:
        cart.pop(index)

    session['cart'] = cart

    flash('Produk dihapus dari keranjang!', 'danger')

    return redirect(url_for('cart'))

# ==================================================
# CHECKOUT
# ==================================================

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():

    cart = session.get('cart', [])

    total = sum(item['harga'] for item in cart)

    if request.method == 'POST':

        nama = request.form['nama']
        alamat = request.form['alamat']

        order = Order(
            nama_pembeli=nama,
            alamat=alamat,
            total=total,
            status='Sedang Diproses'
        )

        db.session.add(order)
        db.session.commit()

        session['cart'] = []

        flash('Checkout berhasil!', 'success')

        return redirect(url_for('orders'))

    return render_template(
        'checkout.html',
        total=total
    )

# ==================================================
# ORDERS
# ==================================================

@app.route('/orders')
def orders():

    orders = Order.query.order_by(
        Order.id.desc()
    ).all()

    return render_template(
        'orders.html',
        orders=orders
    )

# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route('/admin')
def admin():

    products = Product.query.all()

    orders = Order.query.all()

    return render_template(
        'admin.html',
        products=products,
        orders=orders
    )

# ==================================================
# ADD PRODUCT
# ==================================================

@app.route('/add_product', methods=['POST'])
def add_product():

    nama = request.form['nama']
    harga = request.form['harga']
    stok = request.form['stok']
    deskripsi = request.form['deskripsi']

    file = request.files['gambar']

    filename = secure_filename(file.filename)

    if filename == '':
        flash('Gambar belum dipilih!', 'danger')
        return redirect(url_for('admin'))

    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    file.save(filepath)

    product = Product(
        nama=nama,
        harga=harga,
        stok=stok,
        deskripsi=deskripsi,
        gambar=filename
    )

    db.session.add(product)
    db.session.commit()

    flash('Produk berhasil ditambahkan!', 'success')

    return redirect(url_for('admin'))

# ==================================================
# UPDATE STATUS
# ==================================================

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):

    order = Order.query.get_or_404(id)

    order.status = request.form['status']

    db.session.commit()

    flash('Status pesanan berhasil diperbarui!', 'success')

    return redirect(url_for('admin'))

# ==================================================
# MAIN
# ==================================================

if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

with app.app_context():
    db.create_all()

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host='0.0.0.0',
        port=port
    )
