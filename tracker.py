from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from datetime import datetime
import mysql.connector
import os
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Connect to MySQL database
conn = mysql.connector.connect(
    host='localhost',
    user='tanishq',
    password='tmkc1014',
    database='expenses_db'
)
cursor = conn.cursor()

# Create tables if not exist
cursor.execute('''CREATE TABLE IF NOT EXISTS incomes
             (id INT AUTO_INCREMENT PRIMARY KEY, 
              user_id INT, 
              amount FLOAT, 
              date DATE,
              FOREIGN KEY (user_id) REFERENCES users(id))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS expenses
             (id INT AUTO_INCREMENT PRIMARY KEY, 
              user_id INT, 
              description TEXT, 
              amount FLOAT, 
              date DATE,
              FOREIGN KEY (user_id) REFERENCES users(id))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL
            )''')

conn.commit()

@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

# Define a route for the homepage
@app.route('/')
def homepage():
    return render_template('home.html')

# Home route
@app.route('/index')
def index():
    if g.user:
        cursor.execute("SELECT SUM(amount) FROM incomes WHERE user_id = %s", (g.user['id'],))
        row = cursor.fetchone()
        income = float(row[0]) if row[0] else 0

        cursor.execute("SELECT * FROM expenses WHERE user_id = %s", (g.user['id'],))
        expenses = cursor.fetchall()

        return render_template('index.html', income=income, expenses=expenses)
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# Add Income route
@app.route('/add_income', methods=['POST'])
def add_income():
    if g.user:
        try:
            income = float(request.form['income'])
            date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("DELETE FROM incomes WHERE user_id = %s", (g.user['id'],))
            cursor.execute("INSERT INTO incomes (user_id, amount, date) VALUES (%s, %s, %s)", (g.user['id'], income, date))
            conn.commit()
            flash('Income added successfully!', 'success')
        except ValueError:
            flash('Invalid input. Please enter a valid number for income.', 'error')
        return redirect(url_for('index'))
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# Add Expense route
@app.route('/add_expense', methods=['POST'])
def add_expense():
    if g.user:
        try:
            description = request.form['description']
            amount = float(request.form['amount'])
            date = datetime.now().strftime('%Y-%m-%d')

            cursor.execute("INSERT INTO expenses (user_id, description, amount, date) VALUES (%s, %s, %s, %s)",
                           (g.user['id'], description, amount, date))
            conn.commit()
            flash('Expense added successfully!', 'success')
        except ValueError:
            flash('Invalid input. Please enter a valid number for the expense amount.', 'error')

        return redirect(url_for('index'))
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# View Expenses route
@app.route('/view_expenses')
def view_expenses():
    if g.user:
        cursor.execute("SELECT * FROM expenses WHERE user_id = %s", (g.user['id'],))
        expenses = cursor.fetchall()
        return render_template('view_expenses.html', expenses=expenses)
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# Check Savings route
@app.route('/check_savings')
def check_savings():
    if g.user:
        cursor.execute("SELECT SUM(amount) FROM incomes WHERE user_id = %s", (g.user['id'],))
        row = cursor.fetchone()
        income = float(row[0]) if row[0] else 0

        cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s", (g.user['id'],))
        row = cursor.fetchone()
        total_expenses = float(row[0]) if row[0] else 0

        total_savings = income - total_expenses
        return render_template('check_savings.html', total_savings=total_savings)
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# Generate Graph route
@app.route('/generate_graph')
def generate_graph():
    if g.user:
        cursor.execute("SELECT date, amount FROM expenses WHERE user_id = %s", (g.user['id'],))
        data = cursor.fetchall()
        
        dates = [row[0] for row in data]
        amounts = [row[1] for row in data]

        plt.figure(figsize=(10, 6))
        plt.plot(dates, amounts, marker='o', linestyle='-')
        plt.xlabel('Date')
        plt.ylabel('Expense Amount')
        plt.title('Expense Tracking Line Chart')
        plt.xticks(rotation=45)
        
        img_buf = BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        img_base64 = base64.b64encode(img_buf.getvalue()).decode()

        plt.close()

        return render_template('generate_graph.html', graph_base64=img_base64)
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# Clear Data route
@app.route('/clear_data', methods=['GET', 'POST'])
def clear_data():
    if g.user:
        cursor.execute("DELETE FROM incomes WHERE user_id = %s", (g.user['id'],))
        cursor.execute("DELETE FROM expenses WHERE user_id = %s", (g.user['id'],))
        conn.commit()
        flash('Data cleared successfully!', 'info')
        return redirect(url_for('index'))
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# Clear Data Confirmation route
@app.route('/clear_data_confirmation', methods=['POST'])
def clear_data_confirmation():
    if g.user:
        return render_template('clear_data_confirmation.html')
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                           (username, email, password_hash.decode('utf-8')))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash('Error in registration. Please try again.', 'error')
            print(err)
    return render_template('signup.html')    

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error message variable
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch user from database by username
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            # Check if the entered password matches the hashed password
            if bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                # Store user info in session and redirect to home
                session['user'] = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2]
                }
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid username or password. Please try again.'
        else:
            error = 'User does not exist. Please sign up.'

    return render_template('login.html', error=error)
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)

# Close the database connection when the application exits
conn.close()

