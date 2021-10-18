import sqlite3
import time
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import sys
import logging

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('app.log')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)
conn_counter = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global conn_counter
    connection = sqlite3.connect('database.db')
    connection.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    );''')
    connection.row_factory = sqlite3.Row
    conn_counter += 1
    app.config['DB_CONN_COUNTER'] +=1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    if post is not None:
        app.logger.debug(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, Article "{post[2]}" is retrived!')
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
        app.logger.debug(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, A non-existing article is accessed, 404')
        return render_template('404.html'), 404
    else:
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, The "About Us" page is retrieved.')
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
            app.logger.info(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, A new article "{title}" is created.')
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
            app.logger.info(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, Healthy')
            return response
        else:
            response = respond(status=500,result="ERROR - unhealthy")
            app.logger.info(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, unhealthy')
            return response

    except:
        response = respond(status=500,result="ERROR - unhealthy")
        app.logger.info(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, unhealthy')
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
    app.logger.info(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())}, Accesing metrics')
    return response

# start the application on port 3111
if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout,filename='app.log',level=logging.DEBUG)
    app.run(host='0.0.0.0',port='3111')
