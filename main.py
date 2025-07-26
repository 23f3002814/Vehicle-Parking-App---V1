from flask import  request, render_template, redirect, flash,session,url_for
from database import app, db, User, ParkingLot, BookingHistory, create_auto_admin, ParkingSpot
from datetime import datetime
@app.route("/",methods=['GET', 'POST'])
def Home():
    return render_template('home.html')



@app.route('/login', methods=['GET', 'POST'])  
def show_login():
    if request.method == 'GET':
        return render_template('login.html')  

    if request.method == 'POST':
        user = request.form.get('username')
        password = request.form.get('password')

        found_user = User.query.filter_by(username=user).first()

        if found_user:
            if found_user.is_admin:
                session['username'] = found_user.username
                return redirect('/admin_dashboard')
            elif found_user.password == password:
                session['username'] = found_user.username
                return redirect(f'/dashboard/{user}')
            else:
                flash('Password is incorrect')
                return render_template('login.html')
        else:
            flash('User not found. Please register.')
            return redirect('/register')



@app.route('/register', methods=['GET', 'POST'])    
def sign_up():
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':
        formuser = request.form.get('username')
        formpassword = request.form.get('password')
        formpincode=request.form.get('pincode')
        formaddress=request.form.get('address')

        existing_user = User.query.filter_by(username=formuser).first()
        if existing_user:
            flash('User already exists. Please use a different username.')
            return redirect('/register')
        else:
            new_user = User(username=formuser, password=formpassword, is_admin=False,pincode=formpincode,address=formaddress)
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully. Please log in.')
            return redirect('/login')
        
@app.route('/dashboard/<string:username>')
def dashboard(username):
    user = User.query.filter_by(username=username).first()
    parking_lots = ParkingLot.query.all()
    bookings = BookingHistory.query.filter_by(user_id=user.id).all()
    return render_template('user_dashboard.html', username=username, parking_lots=parking_lots, bookings=bookings)




@app.route('/reserve/<int:lot_id>/<string:username>', methods=['GET', 'POST'])
def show_reserve_form(lot_id, username):
    user = User.query.filter_by(username=username).first()
    lot = ParkingLot.query.get(lot_id)
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()

    if not user or not lot or not spot:
        flash("No available spot for this lot.")
        return redirect(url_for('dashboard',username=username) )

    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')
        spot.status='O'
        lot.available_spots += 1 
        
        

        booking = BookingHistory(
            user_id=user.id,
            lot_id=lot.id,
            spot_id=spot.id,
            start_time=datetime.now(),

            vehicle_number=vehicle_number
        )
        

        db.session.add(booking)
        db.session.commit()

        flash(f"Spot {spot.id} reserved successfully! Parking has started.")

        
        return redirect(url_for('dashboard',username=username) )
    return render_template('reserve_form.html', lot=lot, spot=spot, username=username)


@app.route('/release/<int:booking_id>/<string:username>', methods=['POST'])
def release_spot(booking_id, username):
    booking = BookingHistory.query.get(booking_id)

    if not booking or booking.end_time:
        flash("Invalid or already released")
        return redirect(url_for('dashboard', username=username))
        


    booking.end_time = datetime.now()
    duration_hrs = (booking.end_time - booking.start_time).total_seconds() / 3600

    lot = ParkingLot.query.get(booking.lot_id)
    booking.cost = round(duration_hrs * lot.price, 2)

    spot = ParkingSpot.query.get(booking.spot_id)
    spot.status = 'A'
    lot.available_spots += 1 

    db.session.commit()

    flash(f"Spot released. Total cost: ₹{booking.cost}")
    return redirect(url_for('dashboard', username=username))





        
        
@app.route('/summary/<string:username>')
def summary(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found.")
        return redirect(url_for('show_login'))

    bookings = BookingHistory.query.filter_by(user_id=user.id).all()

    # Calculate summary
    total_hours = 0
    total_cost = 0
    
    labels = []
    costs = []
    
    for b in bookings:
        if b.end_time:
            duration = (b.end_time - b.start_time).total_seconds() / 3600
            total_hours += duration
            total_cost += b.cost
            
            labels.append(b.start_time.strftime('%d %b %Y'))  # Format date nicely
            costs.append(b.cost)

    return render_template('summary.html', 
                           username=username, 
                           total_hours=total_hours, 
                           total_cost=total_cost, 
                           bookings=bookings,
                           labels=labels,
                           costs=costs)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('show_login')) 

      


@app.route('/admin_dashboard')
def admin_dashboard():
    parking_lots = ParkingLot.query.all()
    return render_template('admin_dashboard.html', parking_lots=parking_lots, )

@app.route('/admin/add_lot', methods=['GET', 'POST'])
def add_parking_lot():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        price = float(request.form.get('price'))
        max_spots = int(request.form.get('max_spots'))
        

        new_lot = ParkingLot(name=name, location=location, price=price, available_spots=max_spots)
        db.session.add(new_lot)
        db.session.commit()

        for _ in range(max_spots):
            spot = ParkingSpot(lot_id=new_lot.id)
            db.session.add(spot)
        db.session.commit()

        flash('Parking lot added successfully.')
        return redirect('/admin_dashboard')

    return render_template('add_parking_lot.html')

@app.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if request.method == 'POST':
        lot.name = request.form['name']
        lot.location = request.form['location']
        lot.price = float(request.form['price'])
        lot.total_spots = request.form['total_spots']
        db.session.commit()
        flash('Lot updated successfully.')
        return redirect('/admin_dashboard')
    return render_template('edit_lot.html', lot=lot)

@app.route('/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    occupied = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').first()
    if occupied:
        flash('Cannot delete lot with occupied spots.')
        return redirect('/admin_dashboard')
    
    ParkingSpot.query.filter_by(lot_id=lot_id).delete()
    lot = ParkingLot.query.get(lot_id)
    db.session.delete(lot)
    db.session.commit()
    flash('Lot deleted.')
    return redirect('/admin_dashboard')

@app.route('/view_spots/<int:lot_id>')
def view_spots(lot_id):
    selected_lot = ParkingLot.query.get(lot_id)
    
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()

    spot_info = []

    for spot in spots:
        user = None
        vehicle_number = None
        if spot.status == 'O':
            # Get the latest booking entry for this spot
            latest_booking = BookingHistory.query.filter_by(spot_id=spot.id).order_by(BookingHistory.id.desc()).first()
            if latest_booking:
                user = latest_booking.user
                vehicle_number = latest_booking.vehicle_number
        spot_info.append({
            'id': spot.id,
            'status': spot.status,
            'user': user,
            'vehicle_number': vehicle_number
        })

    return render_template(
        'admin_view_spot.html',
        selected_lot=selected_lot,
        parking_spots=spot_info
    )


@app.route('/admin_users')
def show_users():
    users = User.query.filter_by(is_admin=False).all()

    # Prepare a dictionary mapping user_id -> set of vehicle_numbers
    user_vehicles = {}
    for user in users:
        bookings = BookingHistory.query.filter_by(user_id=user.id).all()
        vehicles = [booking.vehicle_number for booking in bookings]
        user_vehicles[user.id] = vehicles

    return render_template('admin_users.html', users=users, user_vehicles=user_vehicles)

    
@app.route('/admin/dashboard/summary')
def admin_summary():
    # Fetch parking data
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    unoccupied_spots = total_spots - occupied_spots

    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(BookingHistory.cost)).scalar() or 0

    return render_template('admin_summary.html',
                           occupied=occupied_spots,
                           unoccupied=unoccupied_spots,
                           total_revenue=total_revenue)



if __name__ == '__main__':
    create_auto_admin()
    app.run(debug=True)