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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)