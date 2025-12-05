from flask import Flask, render_template, request, redirect, url_for
from models import db, Item, User
from datetime import datetime, timedelta
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_bcrypt import Bcrypt
import plotly
import plotly.graph_objects as go
import json

# --- App Setup ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SECRET_KEY'] = 'supersecretkey'

db.init_app(app)
bcrypt = Bcrypt(app)

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Routes ---
@app.route('/')
@login_required
def index():
    today = datetime.utcnow().date()
    soon = today + timedelta(days=3)
    items = Item.query.filter_by(user_id=current_user.id).order_by(Item.expiration_date).all()

    for item in items:
        if item.expiration_date:
            item.is_expiring = (item.expiration_date.date() <= soon)
        else:
            item.is_expiring = False

    return render_template('index.html', items=items, today=today)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        category = request.form['category']
        expiration_str = request.form['expiration_date']
        expiration_date = datetime.strptime(expiration_str, '%Y-%m-%d') if expiration_str else None

        new_item = Item(
            name=name,
            quantity=quantity,
            category=category,
            expiration_date=expiration_date,
            user_id=current_user.id
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_item.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    item = Item.query.get_or_404(id)

    # Prevent users from editing someone else's items
    if item.user_id != current_user.id:
        return redirect(url_for('index'))

    if request.method == 'POST':
        item.name = request.form['name']
        item.quantity = int(request.form['quantity'])
        item.category = request.form['category']

        # Handle optional expiration date
        expiration_str = request.form['expiration_date']
        item.expiration_date = (
            datetime.strptime(expiration_str, '%Y-%m-%d')
            if expiration_str else None
        )

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_item.html', item=item)


@app.route('/delete/<int:id>')
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('index'))


# --- Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- Dashboard Analytics ---
@app.route('/dashboard')
@login_required
def dashboard():
    user_items = Item.query.filter_by(user_id=current_user.id).all()
    categories = [item.category for item in user_items]
    category_counts = {cat: categories.count(cat) for cat in set(categories)}

    fig = go.Figure([go.Bar(x=list(category_counts.keys()), y=list(category_counts.values()))])
    fig.update_layout(title='Items by Category', xaxis_title='Category', yaxis_title='Count')

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('dashboard.html', graph_json=graph_json)


# --- Initialize Database ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


