from flask import Flask, render_template, request, jsonify, redirect
from flask_httpauth import HTTPBasicAuth
from datetime import datetime, datetime as dt, timedelta
import sqlite3

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == 'admin' and password == 'password':
        return True
    return False

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%m/%d/%Y %I:%M %p'):
    return dt.strptime(value, '%Y-%m-%d %H:%M:%S').strftime(format)

def initialize_db():
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 headline TEXT, body TEXT, facts TEXT,
                 timestamp TEXT, stage TEXT)''')
    conn.commit()
    conn.close()

initialize_db()

# Function to update article stages
def update_article_stages(c):
    c.execute("SELECT id, timestamp, stage FROM articles")
    articles_to_update = c.fetchall()
    for article in articles_to_update:
        article_id, timestamp, stage = article
        timestamp_dt = dt.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        time_now = dt.now()
        time_diff = time_now - timestamp_dt

        if stage == 'Hot' and time_diff > timedelta(hours=24):
            c.execute("UPDATE articles SET stage='Cold' WHERE id=?", (article_id,))

@app.route('/')
def reader_home():
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    update_article_stages(c)  # Call the function to update article stages
    c.execute("SELECT * FROM articles ORDER BY timestamp DESC")
    articles = c.fetchall()
    conn.commit()  # Commit the changes made by update_article_stages
    conn.close()
    return render_template('reader_home.html', articles=articles)

@app.route('/home')
@auth.login_required
def home():
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    update_article_stages(c)  # Call the function to update article stages
    c.execute("SELECT * FROM articles ORDER BY timestamp DESC")
    articles = c.fetchall()
    conn.commit()  # Commit the changes made by update_article_stages
    conn.close()
    return render_template('home.html', articles=articles)

@app.route('/submit', methods=['GET', 'POST'])
def submit_article():
    if request.method == 'POST':
        headline = request.form['headline']
        body = request.form['body']
        facts = request.form['facts']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stage = 'Hot'

        conn = sqlite3.connect('articles.db')
        c = conn.cursor()
        c.execute("INSERT INTO articles (headline, body, facts, timestamp, stage) VALUES (?, ?, ?, ?, ?)",
                  (headline, body, facts, timestamp, stage))
        conn.commit()
        conn.close()

        return jsonify({'status': 'Article submitted!'})

    return render_template('index.html')

@app.route('/article/<int:article_id>', methods=['GET'])
def view_article(article_id):
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute("SELECT * FROM articles WHERE id=?", (article_id,))
    article = c.fetchone()
    conn.close()
    return render_template('article.html', article=article)

@app.route('/edit/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        updated_headline = request.form['headline']
        updated_body = request.form['body']
        updated_facts = request.form['facts']

        c.execute("UPDATE articles SET headline=?, body=?, facts=? WHERE id=?",
                  (updated_headline, updated_body, updated_facts, article_id))
        conn.commit()
        conn.close()
        
        return redirect('/')
    
    c.execute("SELECT * FROM articles WHERE id=?", (article_id,))
    article = c.fetchone()
    conn.close()
    
    return render_template('edit.html', article=article)

@app.route('/delete/<int:article_id>', methods=['GET'])
def delete_article(article_id):
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute("DELETE FROM articles WHERE id=?", (article_id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
