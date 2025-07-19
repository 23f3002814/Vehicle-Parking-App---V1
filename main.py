from flask import Flask, request, render_template, redirect,flash
from database import app, db, User, ParkingLot, BookingHistory, create_auto_admin,ParkingSpot


@app.route("/")
def default():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])  
def show_login():
    if request.method == 'GET':
        return render_template('login.html')  

    if request.method == 'POST':
        user = request.form.get('username')
        password = request.form.get('password')

        found_user = User.query.filter_by(username=user).first() #"Find the first user in the database whose username matches the given user

        if found_user:
             if found_user.is_admin:
                    return redirect('/admin_dashboard')
                
             elif found_user.password == password:
                return redirect(f'/dashboard/{user}')
             else:
                return render_template('login.html', error='Password is incorrect')
        else:
            return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])    
def sign_up():
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':
        formuser = request.form.get('username')
        formpassword = request.form.get('password')

        existing_user = User.query.filter_by(username=formuser).first() #o check if a user with the given username (formuser) already exists in the database.
        if existing_user:
            print('User already exists, please use different username')
            return redirect('/register')
        else:
            new_user = User(username=formuser, password=formpassword,is_admin=False)
            db.session.add(new_user)
            db.session.commit()
            print('User created successfully')
            return redirect('/login')

#  user dashboard
@app.route('/dashboard/<string:user>')
def dashboard(user):
    return render_template('user_dashboard.html', username=user)

#  Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    parking_lots = ParkingLot.query.all()
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin_dashboard.html', parking_lots=parking_lots, users=users)

@app.route('/admin/add_lot', methods=['GET', 'POST'])
def add_parking_lot():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        price = float(request.form.get('price'))
        max_spots = int(request.form.get('max_spots'))

        # Create parking lot
        new_lot = ParkingLot(name=name, location=location, price=price, available_spots=max_spots)
        db.session.add(new_lot)
        db.session.commit()

        # Create spots
        for _ in range(max_spots):
            spot = ParkingSpot(lot_id=new_lot.id)
            db.session.add(spot)
        db.session.commit()

        return redirect('/admin_dashboard')

    return render_template('add_parking_lot.html')

@app.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if request.method == 'POST':
        lot.name = request.form['name']
        lot.location = request.form['location']
        lot.price = float(request.form['price'])
        lot.total_spots=request.form['total_spots']
        db.session.commit()
        return redirect('/admin_dashboard')
    return render_template('edit_lot.html', lot=lot)

@app.route('/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    lot = ParkingLot.query.get(lot_id)

    # Delete associated spots first
    ParkingSpot.query.filter_by(lot_id=lot_id).delete()

    # Then delete the lot
    db.session.delete(lot)
    db.session.commit()
    return redirect('/admin_dashboard')

if __name__ == '__main__':
    create_auto_admin()
    app.run(debug=True)
