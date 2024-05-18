import unittest
from flask import Flask, session
from tracker import app, db, cursor  
import mysql.connector
from datetime import datetime

class FlaskExpenseTrackerTestCase(unittest.TestCase):

    def setUp(self):
        
        self.app = app.test_client()
        self.app.testing = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        
        self.conn = mysql.connector.connect(
            host='test_host',
            user='test_user',
            password='test_password',
            database='test_database'
        )
        self.cursor = self.conn.cursor()

    def tearDown(self):
        
        self.cursor.close()
        self.conn.close()

    def test_homepage(self):
        
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the Expense Tracker', response.data)

    def test_index(self):
        
        response = self.app.get('/index')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Total Income', response.data)

    def test_add_income(self):
        
        response = self.app.post('/add_income', data=dict(income='1000'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Income added successfully!', response.data)

    def test_add_expense(self):
        
        response = self.app.post('/add_expense', data=dict(description='Groceries', amount='50'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Expense added successfully!', response.data)

    def test_view_expenses(self):
        
        response = self.app.get('/view_expenses')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'List of Expenses', response.data)

    def test_check_savings(self):
        
        response = self.app.get('/check_savings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Total Savings', response.data)

    def test_generate_graph(self):
        
        response = self.app.get('/generate_graph')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Expense Tracking Line Chart', response.data)

    def test_clear_data(self):
        
        response = self.app.post('/clear_data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Data cleared successfully!', response.data)

    def test_signup(self):
        
        response = self.app.post('/signup', data=dict(username='testuser', email='test@example.com', password='testpassword'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful!', response.data)

    def test_login_logout(self):
        # Test the login and logout routes
        # First, create a user in the test database
        self.cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                            ('testuser', 'test@example.com', 'testpasswordhash'))
        self.conn.commit()
        # Then, attempt to log in
        response = self.app.post('/login', data=dict(username='testuser', password='testpassword'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful!', response.data)
        # Now, test logging out
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user'] = {'id': 1, 'username': 'testuser', 'email': 'test@example.com'}
            response = c.get('/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'You have been logged out.', response.data)
            self.assertNotIn('user', session)

# Run the tests
if __name__ == '__main__':
    unittest.main()
