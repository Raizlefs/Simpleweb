import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from dotenv import load_dotenv
from .models import db, User

load_dotenv()

# Determine paths for templates
basedir = os.path.abspath(os.path.dirname(__file__))
# Templates are in the parent directory relative to 'api/'
template_dir = os.path.join(os.path.dirname(basedir), 'templates')

app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
# Handle DATABASE_URL from Vercel/Postgres (ensure postgresql:// instead of postgres://)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

if not database_url:
    basedir = os.path.abspath(os.path.dirname(__file__))
    # Go up one level since we are in /api
    parent_dir = os.path.dirname(basedir)
    instance_path = os.path.join(parent_dir, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    database_url = 'sqlite:///' + os.path.join(instance_path, 'local.db')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for('dashboard'))
    flash('Invalid username or password.')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    return render_template('dashboard.html', users=users)

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = True if request.form.get('is_admin') == 'on' else False
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('create_user'))
            
        new_user = User(username=username, is_admin=is_admin)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully.')
        return redirect(url_for('dashboard'))
    return render_template('create_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        password = request.form.get('password')
        if password:
            user.set_password(password)
        user.is_admin = True if request.form.get('is_admin') == 'on' else False
        db.session.commit()
        flash('User updated successfully.')
        return redirect(url_for('dashboard'))
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete yourself!')
        return redirect(url_for('dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
