import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Automatically create tables for blog posts and student comments
def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                course_tag TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')
        
        # Seed a sample academic discussion point if the database is brand new
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts")
        if cursor.fetchone()[0] == 0:
            conn.execute('''
                INSERT INTO posts (title, content, course_tag, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                "Welcome to the Academic Discussion Hub",
                "Dear students of Vidya Academy, use this space to ask questions regarding our weekly lectures, seminars, and assignments. Ensure your inputs are respectful and concise.",
                "General",
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
        conn.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/discussions', methods=['GET', 'POST'])
def discussions():
    conn = get_db()
    
    # Handle submitting a new discussion point (Admin/Professor feature)
    if request.method == 'POST' and request.form.get('action') == 'new_post':
        title = request.form['title']
        content = request.form['content']
        course_tag = request.form['course_tag'].upper().strip()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        conn.execute('INSERT INTO posts (title, content, course_tag, created_at) VALUES (?, ?, ?, ?)',
                     (title, content, course_tag, created_at))
        conn.commit()
        return redirect(url_for('discussions'))

    # Handle filtering by course tag
    tag_filter = request.args.get('tag')
    if tag_filter:
        posts = conn.execute('SELECT * FROM posts WHERE course_tag = ? ORDER BY id DESC', (tag_filter,)).fetchall()
    else:
        posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    
    # Fetch all comments and organize them by post ID
    all_comments = conn.execute('SELECT * FROM comments ORDER BY id ASC').fetchall()
    comments_by_post = {}
    for comment in all_comments:
        comments_by_post.setdefault(comment['post_id'], []).append(comment)
        
    return render_template('discussions.html', posts=posts, comments_by_post=comments_by_post, selected_tag=tag_filter)

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    student_name = request.form['student_name']
    comment_text = request.form['comment_text']
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if student_name.strip() and comment_text.strip():
        conn = get_db()
        conn.execute('INSERT INTO comments (post_id, student_name, comment_text, created_at) VALUES (?, ?, ?, ?)',
                     (post_id, student_name, comment_text, created_at))
        conn.commit()
        
    return redirect(url_for('discussions'))

from flask import jsonify

# API Route to send all discussions out to the webpage
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

# API Route to receive a brand new topic from you
@app.route('/api/discussions', methods=['POST'])
def add_topic():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if title and content:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO discussions (title, content, created_at) VALUES (?, ?, ?)", (title, content, current_time))
        conn.commit()
        conn.close()
    return jsonify({"success": True})

# API Route to receive a student reply
@app.route('/api/replies', methods=['POST'])
def add_reply():
    data = request.get_json()
    topic_id = data.get('discussion_id')
    author = data.get('author')
    content = data.get('content')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if author and content and topic_id:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO replies (discussion_id, author, content, created_at) VALUES (?, ?, ?, ?)", (topic_id, author, content, current_time))
        conn.commit()
        conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    import os
    # Tell Flask to listen on port 10000 (Render default) and open to the internet (0.0.0.0)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)