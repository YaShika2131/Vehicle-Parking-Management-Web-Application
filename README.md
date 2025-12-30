# Vehicle-Parking-Management-Web-Application

A comprehensive web-based parking management solution built with Flask that enables efficient parking spot allocation, real-time availability tracking, and automated billing for both administrators and end users.

## 🚀 Features

### Admin Dashboard
- **Parking Lot Management**: Create, edit, and delete parking lots with dynamic spot allocation
- **Real-time Monitoring**: Track total lots, available/occupied spots, and system statistics
- **User Management**: View registered users and their active reservations
- **Spot-level Visibility**: Monitor individual parking spots with occupancy status and duration tracking

### User Portal
- **Seamless Booking**: Browse available parking lots and book spots with one click
- **Active Reservations**: View current parking sessions with real-time cost calculation
- **Parking History**: Access past reservations and total costs
- **Smart Billing**: Automatic hourly rate calculation with minimum 1-hour charge

### Technical Features
- RESTful API endpoints for parking lot data and spot search
- Secure authentication with password hashing
- SQLite database with proper relational modeling
- Responsive Bootstrap UI for mobile and desktop
- Session-based user management

## 🛠️ Technologies Used

**Backend:**
- Python 3.x
- Flask (Web Framework)
- SQLAlchemy (ORM)
- SQLite (Database)
- Werkzeug (Security)

**Frontend:**
- HTML5/Jinja2 Templates
- Bootstrap 5.1.3
- Font Awesome 6.0.0
- JavaScript (ES6+)

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/vehicle-parking-management.git
   cd vehicle-parking-management
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:5000`
   - Default admin credentials: `username: admin`, `password: admin123`

## 📁 Project Structure

```
vehicle-parking-management/
│
├── app.py                      # Main application file with routes and models
├── parking_app.db             # SQLite database (auto-generated)
│
├── templates/
│   ├── base.html              # Base template with navbar and alerts
│   ├── index.html             # Landing page
│   ├── login.html             # Login form
│   ├── register.html          # User registration
│   ├── admin_dashboard.html   # Admin statistics and lot management
│   ├── create_lot.html        # Create new parking lot
│   ├── edit_lot.html          # Edit existing lot
│   ├── view_spots.html        # Detailed spot view for admins
│   ├── view_users.html        # User management page
│   └── user_dashboard.html    # User booking and history
│
└── README.md                  # Project documentation
```

## 💾 Database Schema

### User Model
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Secure password storage
- `email`: User email (unique)
- `phone`: Contact number
- `created_at`: Registration timestamp

### ParkingLot Model
- `id`: Primary key
- `prime_location_name`: Location identifier
- `price`: Hourly rate
- `address`: Full address
- `pin_code`: Postal code
- `maximum_number_of_spots`: Total capacity

### ParkingSpot Model
- `id`: Primary key
- `lot_id`: Foreign key to ParkingLot
- `spot_number`: Unique spot identifier (e.g., "LOC-001")
- `status`: 'A' (Available) or 'O' (Occupied)

### ReserveParkingSpot Model
- `id`: Primary key
- `spot_id`: Foreign key to ParkingSpot
- `user_id`: Foreign key to User
- `parking_timestamp`: Check-in time
- `leaving_timestamp`: Check-out time
- `parking_cost_per_hour`: Rate at booking
- `total_cost`: Final calculated cost
- `is_active`: Reservation status

## 🔐 Security Features

- Password hashing using Werkzeug's security utilities
- Session-based authentication
- Role-based access control (Admin/User)
- Protected routes with decorators
- Input validation and sanitization

## 🌐 API Endpoints

### GET `/api/parking_lots`
Returns JSON list of all parking lots with availability

**Response:**
```json
[
  {
    "id": 1,
    "name": "Downtown Plaza",
    "price": 50.0,
    "address": "123 Main St",
    "pin_code": "123456",
    "total_spots": 20,
    "available_spots": 15
  }
]
```

### GET `/api/search_spot?spot_number=DOW-001`
Search for specific spot information

**Response:**
```json
{
  "spot_number": "DOW-001",
  "status": "Occupied",
  "lot_name": "Downtown Plaza",
  "user": "john_doe",
  "parked_since": "2024-12-30 10:30:00"
}
```

## 🎯 Key Functionalities

1. **Dynamic Spot Generation**: Automatically creates parking spots when lot is created
2. **Smart Capacity Management**: Prevents deletion of lots with occupied spots
3. **Automatic Billing**: Calculates costs based on parking duration and hourly rates
4. **Concurrent Booking Prevention**: Ensures spots can't be double-booked
5. **Cascade Deletion**: Properly handles relationships when deleting lots

## 🚧 Future Enhancements

- [ ] Payment gateway integration
- [ ] Email notifications for reservations
- [ ] QR code generation for spot verification
- [ ] Advanced search and filtering
- [ ] Revenue analytics dashboard
- [ ] Mobile app integration
- [ ] Multi-language support
- [ ] Reservation scheduling (future bookings)


## 📝 License
This project is created for educational purposes.

