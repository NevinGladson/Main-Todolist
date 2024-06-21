from flask import Flask, jsonify, redirect, render_template, request, g, url_for
from flask_login import current_user, LoginManager
import datetime
import os
from .db import User
from flask import flash
import logging

# Format today's date as 'YYYY-MM-DD' and store it in today_date
today_date = datetime.datetime.today().strftime ('%Y-%m-%d')

def create_app(test_config=None):
  app = Flask("todolist", instance_relative_config=True)
  
  app.config.from_mapping(
  SECRET_KEY=os.getenv('SECRET_KEY', 'dev_key'), # Use an environment variable for the secret key or a default value
  #DATABASE=os.path.join(app.instance_path, 'todolist'),
    )

# Load configuration from a file if test_config is not provided
  if test_config is None:
      app.config.from_pyfile('config.py', silent=True)
  else:
      
      app.config.from_mapping(test_config)

  # Ensure the instance folder exists
  try:
      os.makedirs(app.instance_path)
  except OSError:
      pass
  
  # Register the tasks blueprint
  from . import tasks 
  app.register_blueprint(tasks.bp)
  
   # Initialize the database
  from . import db 
  db.init_app(app)

# Register the authentication blueprint
  from .auth import auth as auth_blueprint
  app.register_blueprint(auth_blueprint)

# Register the main application blueprint
  from .main import main as main_blueprint
  app.register_blueprint(main_blueprint)

# Set up the Flask-Login extension
  login_manager = LoginManager()
  login_manager.init_app(app)


# Defining a before request handler to set the current user ID in the global object
  @app.before_request
  def before_request():
    g.user_id = current_user.id if current_user.is_authenticated else None
  
  
  # Defining a user loader callback for Flask-Login
  @login_manager.user_loader
  def load_user(user_id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM app_user WHERE id = %s", (user_id,)) #Fetching user through user ID
    user_data = cursor.fetchone()

    if user_data:
        user = User(*user_data) # Creating a User object from the fetched data
        return user
    return None

#Handle sorting of tasks
  @app.route("/sort-tasks", methods=['GET'])
  def sort_tasks():
    user_id = current_user.id if current_user.is_authenticated else None
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    order_by = request.args.get('order_by', 'date_of_task')
    order = request.args.get('order', 'asc').lower()

    print(f"order_by: {order_by}, order: {order}")

    # Validate the order_by parameter to ensure it's safe to include in SQL
    valid_sort_columns = {'date_of_task', 'urgency_id', 'status_id'}
    if order_by not in valid_sort_columns:
        order_by = 'date_of_task'  # Default to a safe field

    # Ensure the order parameter is either 'asc' or 'desc'
    if order not in ['asc', 'desc']:
        order = 'asc'

    conn = db.get_db()  # Assuming db.get_db() is a function to get the database connection
    cursor = conn.cursor()

    query = f"""
        SELECT t.id, t.task, t.date_of_task, t.day, u.urgency, ts.status
        FROM task t
        INNER JOIN urgency u ON t.urgency_id = u.id
        INNER JOIN task_status ts ON t.status_id = ts.id
        WHERE t.user_id = %s
        ORDER BY {order_by} {order}
    """
    cursor.execute(query, (user_id,))
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert tasks to a JSON-friendly format
    tasks_list = [{
        'id': task[0],
        'task': task[1],
        'date_of_task': task[2].isoformat() if task[2] else None,
        'day': task[3],
        'urgency': task[4],
        'status': task[5]
    } for task in tasks]

    return jsonify(tasks=tasks_list)

  @app.route("/index")
  def index():
    user_id = g.user_id = current_user.id if current_user.is_authenticated else None
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = db.get_db()
    cursor = conn.cursor()

    # Handle overdue tasks
    today_date = datetime.datetime.today().strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT INTO overdue_tasks (task, date_of_task, day, points, urgency_id, status_id, user_id)
        SELECT task, date_of_task, day, points, urgency_id, status_id, user_id
        FROM task 
        WHERE date_of_task < %s AND status_id = 2 AND user_id = %s
    """, (today_date, user_id))
    cursor.execute("DELETE FROM task WHERE date_of_task < %s AND user_id = %s", (today_date, user_id))
    conn.commit()

    # Collect filter parameters
    title = request.args.get('title', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    urgencies = request.args.getlist('urgency')
    status = request.args.get('status', '')
    order_by = request.args.get('sort_by', 'date_of_task')
    order = request.args.get('order', 'asc')  # Default to ascending if not specified

    # Validate sort order and column
    valid_sort_columns = {'date_of_task': 't.date_of_task', 'urgency': 'u.urgency', 'status': 'ts.status'}
    db_column = valid_sort_columns.get(order_by, 't.date_of_task')
    valid_orders = {'asc', 'desc'}
    if order not in valid_orders:
        order = 'asc'

    # Build the query dynamically based on filters
    query = f"""
        SELECT t.id, t.task, t.date_of_task, t.day, u.urgency, ts.status 
        FROM task t 
        INNER JOIN urgency u ON t.urgency_id = u.id 
        INNER JOIN task_status ts ON t.status_id = ts.id 
        WHERE t.user_id = %s
    """
    params = [user_id]

    if title:
        query += " AND t.task ILIKE %s"
        params.append(f"%{title}%")
    if start_date:
        query += " AND t.date_of_task >= %s"
        params.append(start_date)
    if end_date:
        query += " AND t.date_of_task <= %s"
        params.append(end_date)
    if status:
        query += " AND ts.id = %s"
        params.append(status)
    if urgencies:
        urgency_conditions = " OR ".join(["u.id = %s" for u in urgencies])
        query += f" AND ({urgency_conditions})"
        params.extend(urgencies)

    query += f" ORDER BY {db_column} {order}"

    cursor.execute(query, params)
    tasks = cursor.fetchall()

    cursor.execute("SELECT id, task FROM overdue_tasks WHERE user_id = %s", (user_id,))
    overdue = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', tasks=tasks, overdue=overdue, order_by=order_by,
                           filter_title=title, filter_start_date=start_date, filter_end_date=end_date,
                           filter_urgencies=urgencies, filter_status=status)

      
  #Handle current week tasks
  @app.route("/weekly")
  def weekly_sched():
    user_id = g.user_id = current_user.id if current_user.is_authenticated else None
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    endweek_date = (datetime.datetime.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.task, t.date_of_task, t.day, u.urgency, ts.status
        FROM task t
        INNER JOIN urgency u ON t.urgency_id = u.id
        INNER JOIN task_status ts ON t.status_id = ts.id
        WHERE t.date_of_task BETWEEN %s AND %s AND t.user_id = %s
        ORDER BY t.date_of_task
    """, (today_date, endweek_date, user_id))
    tasks = cursor.fetchall()
    return jsonify([{
        'id': task[0],
        'task': task[1],
        'date_of_task': task[2].isoformat() if task[2] else '',
        'day': task[3],
        'urgency': task[4],
        'status': task[5]
    } for task in tasks])
    
  @app.route('/delete_overdue_task/<int:id>', methods=['POST'])
  def delete_overdue_task(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM overdue_tasks WHERE id = %s", (id,))
    conn.commit()
    return redirect(url_for('index'))


  





  return app
  


