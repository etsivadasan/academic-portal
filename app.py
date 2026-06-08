import sqlite3
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime

# Tell Flask to look in 'public' for your HTML files
app = Flask(__name__, static_folder='public')

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS discussions (id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, created_at TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY, discussion_id INTEGER, author TEXT, content TEXT, created_at TEXT)')
    conn.commit()
    conn.close()

init_db()

# Serve the main page
@app.route('/')
def index():
    return send_from_directory('public', 'discussions.html')

# API Routes
@app.route('/api/discussions', methods=['GET'])
def get_discussions():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM discussions ORDER BY created_at DESC")
    topics = [dict(row) for row in cursor.fetchall()]
    for topic in topics:
        cursor.execute("SELECT * FROM replies WHERE discussion_id = ? ORDER BY created_at ASC", (topic['id'],))
        topic['replies'] = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(topics)

# ... (Include your other POST routes here) ...

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)