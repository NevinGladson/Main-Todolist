import psycopg2
import click 
from flask import current_app, g
from flask.cli import with_appcontext
import os

# Define the User class to represent a user in the application
class User:
    def __init__(self, id, email, username, password_hash):
        self.id = id
        self.email = email
        self.username = username
        self.password_hash = password_hash

    # Method required by Flask-Login to get the user's ID
    def get_id(self):
        return str(self.id)

    # Property to indicate if the user is authenticated
    @property
    def is_authenticated(self):
        return True

    # Property to indicate if the user is active
    @property
    def is_active(self):
        return True


# Function to get a database connection
def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'todolist'),  # Database name
            user=os.getenv('DB_USER', 'nevin'),  # Database user
            password=os.getenv('DB_PASSWORD', 'chiquitita#2002#'),  # Database password
            host=os.getenv('DB_HOST', 'todolist.c1dflb4y7v2r.us-east-1.rds.amazonaws.com'),  # Database host
            port=os.getenv('DB_PORT', '5432')  # Database port
        )
    return g.db

# Function to close the database connection
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

# Function to initialize the database
def init_db():
    db = get_db()  # Get the database connection
    f = current_app.open_resource("sql/001_list.sql")  # Open the SQL file
    sql_code = f.read().decode("ascii")  # Read and decode the SQL file
    cur = db.cursor()  # Get a cursor to execute SQL commands
    cur.execute(sql_code)  # Execute the SQL code
    cur.close()  # Close the cursor
    db.commit()  # Commit the transaction
    close_db()  # Close the database connection
    
# Define a command-line command to initialize the database
@click.command('initdb', help="initialise the database")
@with_appcontext   
def init_db_command():
    init_db()  # Initialize the database
    click.echo('DB initialised')  # Print a message to the console

# Function to set up the application with database-related commands and hooks
def init_app(app):
    app.teardown_appcontext(close_db)  # Register the function to close the DB connection when the app context ends
    app.cli.add_command(init_db_command)  # Add the initdb command to the app's CLI
