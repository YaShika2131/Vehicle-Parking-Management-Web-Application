"""
Vehicle Parking Management System 
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('ReserveParkingSpot', backref='user', lazy=True)

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(1), default='A')  # A-Available, O-Occupied
    reservations = db.relationship('ReserveParkingSpot', backref='spot', lazy=True)

class ReserveParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime)
    parking_cost_per_hour = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)

# Helper Functions
def create_admin():
    """Create admin user if doesn't exist"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@parking.com',
            phone='1234567890'
        )
        db.session.add(admin)
        db.session.commit()

def is_admin():
    """Check if current user is admin"""
    return session.get('username') == 'admin'

def login_required(f):
    """Decorator for login required routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for admin required routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        user = User(
            username=username,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    parking_lots = ParkingLot.query.all()
    total_lots = len(parking_lots)
    total_spots = sum(lot.maximum_number_of_spots for lot in parking_lots)
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    available_spots = total_spots - occupied_spots
    total_users = User.query.filter(User.username != 'admin').count()
    
    return render_template('admin_dashboard.html', 
                         parking_lots=parking_lots,
                         total_lots=total_lots,
                         total_spots=total_spots,
                         occupied_spots=occupied_spots,
                         available_spots=available_spots,
                         total_users=total_users)

@app.route('/admin/create_lot', methods=['GET', 'POST'])
@login_required
@admin_required
def create_parking_lot():
    if request.method == 'POST':
        lot = ParkingLot(
            prime_location_name=request.form['location_name'],
            price=float(request.form['price']),
            address=request.form['address'],
            pin_code=request.form['pin_code'],
            maximum_number_of_spots=int(request.form['max_spots'])
        )
        
        db.session.add(lot)
        db.session.flush()  # Get the lot.id
        
        # Create parking spots for this lot
        for i in range(1, lot.maximum_number_of_spots + 1):
            spot = ParkingSpot(
                lot_id=lot.id,
                spot_number=f"{lot.prime_location_name[:3].upper()}-{i:03d}",
                status='A'
            )
            db.session.add(spot)
        
        db.session.commit()
        flash('Parking lot created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_lot.html')

@app.route('/admin/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'POST':
        lot.prime_location_name = request.form['location_name']
        lot.price = float(request.form['price'])
        lot.address = request.form['address']
        lot.pin_code = request.form['pin_code']
        new_max_spots = int(request.form['max_spots'])
        
        current_spots = len(lot.spots)
        
        if new_max_spots > current_spots:
            # Add new spots
            for i in range(current_spots + 1, new_max_spots + 1):
                spot = ParkingSpot(
                    lot_id=lot.id,
                    spot_number=f"{lot.prime_location_name[:3].upper()}-{i:03d}",
                    status='A'
                )
                db.session.add(spot)
        elif new_max_spots < current_spots:
            # Remove excess spots (only if they're available)
            spots_to_remove = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').limit(current_spots - new_max_spots).all()
            for spot in spots_to_remove:
                db.session.delete(spot)
        
        lot.maximum_number_of_spots = new_max_spots
        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_lot.html', lot=lot)

@app.route('/admin/delete_lot/<int:lot_id>')
@login_required
@admin_required
def delete_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    # Check if all spots are available
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
    if occupied_spots > 0:
        flash('Cannot delete parking lot with occupied spots!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/view_spots/<int:lot_id>')
@login_required
@admin_required
def view_spots(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    
    spot_details = []
    for spot in spots:
        active_reservation = ReserveParkingSpot.query.filter_by(
            spot_id=spot.id, is_active=True
        ).first()
        
        detail = {
            'spot': spot,
            'reservation': active_reservation,
            'user': active_reservation.user if active_reservation else None
        }
        spot_details.append(detail)
    
    return render_template('view_spots.html', lot=lot, spot_details=spot_details)

@app.route('/admin/users')
@login_required
@admin_required
def view_users():
    users = User.query.filter(User.username != 'admin').all()
    return render_template('view_users.html', users=users)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if is_admin():
        return redirect(url_for('admin_dashboard'))
    
    user_id = session['user_id']
    active_reservations = ReserveParkingSpot.query.filter_by(user_id=user_id, is_active=True).all()
    past_reservations = ReserveParkingSpot.query.filter_by(user_id=user_id, is_active=False).limit(10).all()
    
    parking_lots = ParkingLot.query.all()
    
    return render_template('user_dashboard.html', 
                         active_reservations=active_reservations,
                         past_reservations=past_reservations,
                         parking_lots=parking_lots)

@app.route('/user/book_spot/<int:lot_id>')
@login_required
def book_spot(lot_id):
    if is_admin():
        flash('Admin cannot book spots', 'error')
        return redirect(url_for('admin_dashboard'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    available_spot = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').first()
    
    if not available_spot:
        flash('No available spots in this parking lot!', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Create reservation
    reservation = ReserveParkingSpot(
        spot_id=available_spot.id,
        user_id=session['user_id'],
        parking_cost_per_hour=lot.price,
        is_active=True
    )
    
    # Update spot status
    available_spot.status = 'O'
    
    db.session.add(reservation)
    db.session.commit()
    
    flash(f'Successfully booked spot {available_spot.spot_number}!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/release_spot/<int:reservation_id>')
@login_required
def release_spot(reservation_id):
    reservation = ReserveParkingSpot.query.get_or_404(reservation_id)
    
    if reservation.user_id != session['user_id']:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Calculate total cost
    leaving_time = datetime.utcnow()
    parking_duration = leaving_time - reservation.parking_timestamp
    hours = max(1, parking_duration.total_seconds() / 3600)  # Minimum 1 hour
    total_cost = round(hours * reservation.parking_cost_per_hour, 2)
    
    # Update reservation
    reservation.leaving_timestamp = leaving_time
    reservation.total_cost = total_cost
    reservation.is_active = False
    
    # Update spot status
    reservation.spot.status = 'A'
    
    db.session.commit()
    
    flash(f'Spot released successfully! Total cost: ₹{total_cost}', 'success')
    return redirect(url_for('user_dashboard'))

# API Routes (Optional functionality)
@app.route('/api/parking_lots')
def api_parking_lots():
    lots = ParkingLot.query.all()
    return jsonify([{
        'id': lot.id,
        'name': lot.prime_location_name,
        'price': lot.price,
        'address': lot.address,
        'pin_code': lot.pin_code,
        'total_spots': lot.maximum_number_of_spots,
        'available_spots': len([s for s in lot.spots if s.status == 'A'])
    } for lot in lots])

@app.route('/api/search_spot')
def api_search_spot():
    spot_number = request.args.get('spot_number')
    if not spot_number:
        return jsonify({'error': 'Spot number required'}), 400
    
    spot = ParkingSpot.query.filter_by(spot_number=spot_number).first()
    if not spot:
        return jsonify({'error': 'Spot not found'}), 404
    
    result = {
        'spot_number': spot.spot_number,
        'status': 'Available' if spot.status == 'A' else 'Occupied',
        'lot_name': spot.lot.prime_location_name
    }
    
    if spot.status == 'O':
        active_reservation = ReserveParkingSpot.query.filter_by(
            spot_id=spot.id, is_active=True
        ).first()
        if active_reservation:
            result['user'] = active_reservation.user.username
            result['parked_since'] = active_reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify(result)

# Template Creation Helper
def create_templates():
    """Create all required HTML templates"""
    import os
    
    templates_dir = 'templates'
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Base template
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Vehicle Parking App{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-car"></i> Parking Manager
            </a>
            <div class="navbar-nav ms-auto">
                {% if session.username %}
                    <span class="navbar-text me-3">Welcome, {{ session.username }}!</span>
                    <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                {% else %}
                    <a class="nav-link" href="{{ url_for('login') }}">Login</a>
                    <a class="nav-link" href="{{ url_for('register') }}">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Index template
    index_template = '''{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-lg-8 mx-auto text-center">
        <h1 class="display-4 mb-4">
            <i class="fas fa-parking text-primary"></i>
            Vehicle Parking Management
        </h1>
        <p class="lead mb-4">Efficient parking spot management for administrators and users</p>
        
        <div class="row">
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="fas fa-user-shield text-primary"></i> Admin Access
                        </h5>
                        <p class="card-text">Manage parking lots, spots, and view system statistics</p>
                        <a href="{{ url_for('login') }}" class="btn btn-primary">Admin Login</a>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="fas fa-user text-success"></i> User Access
                        </h5>
                        <p class="card-text">Book and manage your parking reservations</p>
                        <a href="{{ url_for('login') }}" class="btn btn-success me-2">Login</a>
                        <a href="{{ url_for('register') }}" class="btn btn-outline-success">Register</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    # Login template
    login_template = '''{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4><i class="fas fa-sign-in-alt"></i> Login</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
                
                <hr>
                <div class="text-center">
                    <p>Demo Credentials:</p>
                    <small class="text-muted">
                        Admin: username=admin, password=admin123<br>
                        Or <a href="{{ url_for('register') }}">register as a new user</a>
                    </small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    # Register template
    register_template = '''{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4><i class="fas fa-user-plus"></i> Register</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" name="email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Phone</label>
                        <input type="tel" class="form-control" name="phone" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100">Register</button>
                </form>
                
                <div class="text-center mt-3">
                    <a href="{{ url_for('login') }}">Already have an account? Login</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    # Admin Dashboard template
    admin_dashboard_template = '''{% extends "base.html" %}
{% block content %}
<h2><i class="fas fa-tachometer-alt"></i> Admin Dashboard</h2>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <h5>Total Lots</h5>
                <h3>{{ total_lots }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <h5>Total Spots</h5>
                <h3>{{ total_spots }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <h5>Available</h5>
                <h3>{{ available_spots }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <h5>Occupied</h5>
                <h3>{{ occupied_spots }}</h3>
            </div>
        </div>
    </div>
</div>

<div class="d-flex justify-content-between align-items-center mb-3">
    <h4>Parking Lots</h4>
    <div>
        <a href="{{ url_for('create_parking_lot') }}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Create New Lot
        </a>
        <a href="{{ url_for('view_users') }}" class="btn btn-info">
            <i class="fas fa-users"></i> View Users
        </a>
    </div>
</div>

<div class="table-responsive">
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Location</th>
                <th>Address</th>
                <th>Price/Hour</th>
                <th>Total Spots</th>
                <th>Available</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for lot in parking_lots %}
            <tr>
                <td>{{ lot.prime_location_name }}</td>
                <td>{{ lot.address }}, {{ lot.pin_code }}</td>
                <td>₹{{ lot.price }}</td>
                <td>{{ lot.maximum_number_of_spots }}</td>
                <td>{{ lot.spots|selectattr("status", "equalto", "A")|list|length }}</td>
                <td>
                    <a href="{{ url_for('view_spots', lot_id=lot.id) }}" class="btn btn-sm btn-info">View Spots</a>
                    <a href="{{ url_for('edit_parking_lot', lot_id=lot.id) }}" class="btn btn-sm btn-warning">Edit</a>
                    <a href="{{ url_for('delete_parking_lot', lot_id=lot.id) }}" 
                       class="btn btn-sm btn-danger"
                       onclick="return confirm('Are you sure?')">Delete</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}'''

    # Create all template files
    templates = {
        'base.html': base_template,
        'index.html': index_template,
        'login.html': login_template,
        'register.html': register_template,
        'admin_dashboard.html': admin_dashboard_template,
        'create_lot.html': '''{% extends "base.html" %}
{% block content %}
<h2><i class="fas fa-plus"></i> Create Parking Lot</h2>
<form method="POST">
    <div class="row">
        <div class="col-md-6">
            <div class="mb-3">
                <label class="form-label">Location Name</label>
                <input type="text" class="form-control" name="location_name" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Price per Hour (₹)</label>
                <input type="number" step="0.01" class="form-control" name="price" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Maximum Spots</label>
                <input type="number" min="1" class="form-control" name="max_spots" required>
            </div>
        </div>
        <div class="col-md-6">
            <div class="mb-3">
                <label class="form-label">Address</label>
                <textarea class="form-control" name="address" rows="3" required></textarea>
            </div>
            <div class="mb-3">
                <label class="form-label">Pin Code</label>
                <input type="text" class="form-control" name="pin_code" required>
            </div>
        </div>
    </div>
    <button type="submit" class="btn btn-primary">Create Parking Lot</button>
    <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}''',
        'edit_lot.html': '''{% extends "base.html" %}
{% block content %}
<h2><i class="fas fa-edit"></i> Edit Parking Lot</h2>
<form method="POST">
    <div class="row">
        <div class="col-md-6">
            <div class="mb-3">
                <label class="form-label">Location Name</label>
                <input type="text" class="form-control" name="location_name" value="{{ lot.prime_location_name }}" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Price per Hour (₹)</label>
                <input type="number" step="0.01" class="form-control" name="price" value="{{ lot.price }}" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Maximum Spots</label>
                <input type="number" min="1" class="form-control" name="max_spots" value="{{ lot.maximum_number_of_spots }}" required>
            </div>
        </div>
        <div class="col-md-6">
            <div class="mb-3">
                <label class="form-label">Address</label>
                <textarea class="form-control" name="address" rows="3" required>{{ lot.address }}</textarea>
            </div>
            <div class="mb-3">
                <label class="form-label">Pin Code</label>
                <input type="text" class="form-control" name="pin_code" value="{{ lot.pin_code }}" required>
            </div>
        </div>
    </div>
    <button type="submit" class="btn btn-primary">Update Parking Lot</button>
    <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}''',
        'view_spots.html': '''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fas fa-parking"></i> {{ lot.prime_location_name }} - Parking Spots</h2>
    <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">Back to Dashboard</a>
</div>

<div class="row mb-3">
    <div class="col-md-4">
        <div class="card bg-info text-white">
            <div class="card-body">
                <h6>Total Spots</h6>
                <h4>{{ spot_details|length }}</h4>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card bg-success text-white">
            <div class="card-body">
                <h6>Available</h6>
                <h4>{{ spot_details|selectattr("spot.status", "equalto", "A")|list|length }}</h4>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <h6>Occupied</h6>
                <h4>{{ spot_details|selectattr("spot.status", "equalto", "O")|list|length }}</h4>
            </div>
        </div>
    </div>
</div>

<div class="table-responsive">
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Spot Number</th>
                <th>Status</th>
                <th>User</th>
                <th>Parked Since</th>
                <th>Duration</th>
            </tr>
        </thead>
        <tbody>
            {% for detail in spot_details %}
            <tr>
                <td>{{ detail.spot.spot_number }}</td>
                <td>
                    {% if detail.spot.status == 'A' %}
                        <span class="badge bg-success">Available</span>
                    {% else %}
                        <span class="badge bg-warning">Occupied</span>
                    {% endif %}
                </td>
                <td>
                    {% if detail.user %}
                        {{ detail.user.username }}
                    {% else %}
                        -
                    {% endif %}
                </td>
                <td>
                    {% if detail.reservation %}
                        {{ detail.reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M') }}
                    {% else %}
                        -
                    {% endif %}
                </td>
                <td>
                    {% if detail.reservation %}
                        {% set duration = (moment().utcnow() - detail.reservation.parking_timestamp) %}
                        {% set hours = (duration.total_seconds() // 3600)|int %}
                        {% set minutes = ((duration.total_seconds() % 3600) // 60)|int %}
                        {{ hours }}h {{ minutes }}m
                    {% else %}
                        -
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}''',
        'view_users.html': '''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fas fa-users"></i> Registered Users</h2>
    <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">Back to Dashboard</a>
</div>

<div class="table-responsive">
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Joined</th>
                <th>Active Reservations</th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr>
                <td>{{ user.username }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.phone }}</td>
                <td>{{ user.created_at.strftime('%Y-%m-%d') }}</td>
                <td>
                    {% set active_count = user.reservations|selectattr("is_active", "equalto", True)|list|length %}
                    {% if active_count > 0 %}
                        <span class="badge bg-primary">{{ active_count }}</span>
                    {% else %}
                        <span class="badge bg-secondary">0</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}''',
        'user_dashboard.html': '''{% extends "base.html" %}
{% block content %}
<h2><i class="fas fa-user"></i> User Dashboard</h2>

{% if active_reservations %}
<div class="row mb-4">
    <div class="col-12">
        <h4>Active Reservations</h4>
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Spot Number</th>
                        <th>Location</th>
                        <th>Parked Since</th>
                        <th>Rate/Hour</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for reservation in active_reservations %}
                    <tr>
                        <td>{{ reservation.spot.spot_number }}</td>
                        <td>{{ reservation.spot.lot.prime_location_name }}</td>
                        <td>{{ reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>₹{{ reservation.parking_cost_per_hour }}</td>
                        <td>
                            <a href="{{ url_for('release_spot', reservation_id=reservation.id) }}" 
                               class="btn btn-sm btn-warning"
                               onclick="return confirm('Are you sure you want to release this spot?')">
                                Release Spot
                            </a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endif %}

<div class="row">
    <div class="col-md-8">
        <h4>Available Parking Lots</h4>
        <div class="row">
            {% for lot in parking_lots %}
            {% set available_spots = lot.spots|selectattr("status", "equalto", "A")|list|length %}
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">{{ lot.prime_location_name }}</h5>
                        <p class="card-text">
                            <small class="text-muted">{{ lot.address }}</small><br>
                            <strong>Rate:</strong> ₹{{ lot.price }}/hour<br>
                            <strong>Available Spots:</strong> {{ available_spots }}/{{ lot.maximum_number_of_spots }}
                        </p>
                        {% if available_spots > 0 %}
                            <a href="{{ url_for('book_spot', lot_id=lot.id) }}" 
                               class="btn btn-success btn-sm"
                               onclick="return confirm('Book a spot at {{ lot.prime_location_name }}?')">
                                Book Spot
                            </a>
                        {% else %}
                            <button class="btn btn-secondary btn-sm" disabled>No Spots Available</button>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="col-md-4">
        <h4>Recent Parking History</h4>
        {% if past_reservations %}
        <div class="list-group">
            {% for reservation in past_reservations %}
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">{{ reservation.spot.spot_number }}</h6>
                    <small>₹{{ reservation.total_cost or 0 }}</small>
                </div>
                <p class="mb-1">{{ reservation.spot.lot.prime_location_name }}</p>
                <small>{{ reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M') }}</small>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p class="text-muted">No parking history yet.</p>
        {% endif %}
    </div>
</div>
{% endblock %}'''
    }
    
    for filename, content in templates.items():
        with open(os.path.join(templates_dir, filename), 'w') as f:
            f.write(content)

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create admin user
        create_admin()
        
        # Create templates
        create_templates()
        
        print(" Database created successfully!")
        print(" Admin user created (username: admin, password: admin123)")
        print(" Templates created successfully!")
        print(" Starting Flask application...")
    
    app.run(debug=True)