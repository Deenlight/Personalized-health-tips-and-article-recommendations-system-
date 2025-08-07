import os
import csv
from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import pandas as pd


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session handling

# Categories for health preferences
categories = [
    "Fitness", "Nutrition", "Mental Health", "Chronic Illness", "Sleep Health",
    "Immunity", "Stress Relief", "Dietary Tips", "Exercise", "Healthy Lifestyle"
]

# Ensure 'users.csv' is created with the correct header
def initialize_users_csv():
    if not os.path.exists('users.csv'):
        with open('users.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'email', 'password', 'preferences'])

# Ensure 'viewed_recommendations.csv' is created with the correct header
def initialize_viewed_recommendations_csv():
    if not os.path.exists('viewed_recommendations.csv'):
        with open('viewed_recommendations.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['user_email', 'recommendation_id', 'timestamp'])

# Initialize CSV files
initialize_users_csv()
initialize_viewed_recommendations_csv()

# Load the health tips dataset
health_tips_df = pd.read_csv('health_tips.csv')

# Landing page route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip().lower()  # Get the search query and normalize it

    # Check if the query is empty
    if not query:
        return render_template('search_results.html', results=[], query=query)

    # Filter the DataFrame based on title or category
    results = health_tips_df[
        health_tips_df['title'].str.lower().str.contains(query) |
        health_tips_df['category'].str.lower().str.contains(query)
    ]

    # Convert results to a list of dictionaries for rendering
    results_list = results.to_dict(orient='records')

    return render_template('search_results.html', results=results_list, query=query)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        preferences = request.form.getlist('preferences')

        # Save user details to users.csv
        with open('users.csv', mode='a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, email, password, ','.join(preferences)])

        return redirect('/login')
    return render_template('register.html', categories=categories)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Verify credentials from users.csv
        with open('users.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['email'] == email and row['password'] == password:
                    session['user_email'] = email
                    return redirect('/recommendations')

        return "Invalid email or password", 401
    return render_template('login.html')

# Recommendations route
@app.route('/recommendations')
def recommendations():
    user_email = session.get('user_email')
    if not user_email:
        return redirect('/login')

    # Get user preferences
    user_preferences = []
    with open('users.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['email'] == user_email:
                user_preferences = row['preferences'].split(',')
                break

    # Filter recommendations based on preferences
    recommendations = []
    with open('health_tips.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['category'] in user_preferences:
                recommendations.append(row)

    return render_template('recommendations.html', recommendations=recommendations)

# View recommendation route
@app.route('/recommendation/<int:rec_id>', methods=['GET'])
def view_recommendation(rec_id):
    user_email = session.get('user_email')
    if not user_email:
        return redirect('/login')

    # Log the recommendation as viewed
    with open('viewed_recommendations.csv', mode='a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([user_email, rec_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

    # Find the recommendation details
    with open('health_tips.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row['id']) == rec_id:
                return render_template('view_recommendation.html', recommendation=row)

    return "Recommendation not found", 404

# Update preferences route
@app.route('/update_preferences', methods=['GET', 'POST'])
def update_preferences():
    user_email = session.get('user_email')
    if not user_email:
        return redirect('/login')

    if request.method == 'POST':
        new_preferences = request.form.getlist('preferences')

        # Update preferences in users.csv
        users = []
        with open('users.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['email'] == user_email:
                    row['preferences'] = ','.join(new_preferences)
                users.append(row)

        with open('users.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['username', 'email', 'password', 'preferences'])
            writer.writeheader()
            writer.writerows(users)

        return redirect('/recommendations')

    # Render preferences form with current preferences pre-checked
    current_preferences = []
    with open('users.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['email'] == user_email:
                current_preferences = row['preferences'].split(',')
                break

    return render_template('update_preferences.html', categories=categories, current_preferences=current_preferences)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
 