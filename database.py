from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vehiclepark.db"
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    
class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available_spots = db.Column(db.Integer, default=0)

class BookingHistory(db.Model):
    __tablename__ = 'booking_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'))
    spot_id = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    cost = db.Column(db.Float)

    user = db.relationship('User', backref='bookings')
    lot = db.relationship('ParkingLot', backref='bookings')

with app.app_context():
    db.create_all()

def create_auto_admin():
    with app.app_context():
        db.create_all()
        if_exists = User.query.filter_by(is_admin=True).first()
        if not if_exists:
            admin = User(username='admin', password='admin123', is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print('Admin created')
        else:
            print('Admin already exists')

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # A = Available, O = Occupied

    lot = db.relationship('ParkingLot', backref='spots')
with app.app_context():
    db.create_all()
