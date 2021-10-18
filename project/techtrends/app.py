import sqlite3
from sqlite3.dbapi2 import DatabaseError, OperationalError
import time
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash, logging 
from werkzeug.exceptions import abort
import sys, os
import logging

def initialize_logger():
    
    log_level = os.getenv("LOGLEVEL", "DEBUG").upper()
    log_level = (
        getattr(logging, log_level)
        if log_level in ["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING",]
        else logging.DEBUG
    )

    # logger = logging.getLogger(__name__)
    format='%(levelname)s:%(name)s:%(asctime)s, %(message)s'
    formatter = logging.Formatter(format)
    app.logger.setLevel(log_level)
    fh = logging.FileHandler('app.log')
    sh = logging.StreamHandler()

    fh.setLevel(log_level)
    sh.setLevel(log_level)
    
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)

    app.logger.addHandler(fh)
    app.logger.addHandler(sh)

    # logging.basicConfig(stream=sys.stdout,filename='app.log',
    #     format='%(levelname)s:%(name)s:%(asctime)s, %(message)s',
    #             level=log_level,
    # )
    

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    try:
        connection.execute('SELECT * FROM posts').fetchall()
        return connection
    except OperationalError:
        app.logger.critical("Post table not found.")
    finally:
        connection.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        );''')
        connection.row_factory = sqlite3.Row
        app.config['DB_CONN_COUNTER'] +=1
        app.logger.info("Post table created.")
        return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    if post is not None:
        app.logger.info(' Article "{post[2]}" is retrived!')
    connection.close()
    return post

# dynamic response
def respond(status=200,result="OK - healthy"):
    response = app.response_class(
                    response = json.dumps({"result":result}),
                    status=status,
                    mimetype='application/json'
            )
    return response

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'seven monkeys on ropes'
app.config['DB_CONN_COUNTER'] = 0
# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warning('A non-existing article is accessed, 404')
        return render_template('404.html'), 404
    else:
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us" page is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            app.logger.info(' A new article "{title}" is created.')
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def health():
    try:
        connection = get_db_connection()
        posts=connection.execute('SELECT count(id) FROM posts').fetchall()[0][0]
        print(posts)
        connection.close()
        if int(posts)>0:
            response = respond(status=200,result="OK - healthy")
            app.logger.info('Healthy')
            return response
        else:
            response = respond(status=500,result="ERROR - unhealthy")
            app.logger.warning('Unhealthy')
            return response

    except:
        response = respond(status=500,result="ERROR - unhealthy")
        app.logger.warning('Unhealthy')
        return response
    
    

@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts=connection.execute('SELECT count(id) FROM posts').fetchall()[0][0]
    connection.close()
    response = app.response_class(
        response=json.dumps({"db_connection_count": app.config['DB_CONN_COUNTER'], "post_count": posts}),
            status=200,
            mimetype='application/json'
    )
    app.logger.info('Accesing metrics')
    return response

# start the application on port 3111
if __name__ == "__main__":
    initialize_logger()
    
    # logging.basicConfig(stream=sys.stdout,filename='app.log',level=logging.DEBUG)
    app.run(host='0.0.0.0',port='3111')
