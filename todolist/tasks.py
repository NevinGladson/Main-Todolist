from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from flask_login import current_user
from datetime import datetime

from . import __init__
from . import db



bp = Blueprint("todolist", "todolist", url_prefix="/task")

@bp.before_request
def before_request():
    g.user_id = current_user.id if current_user.is_authenticated else None  

#user_id = g.user_id

def day(date_of_task):
  date = datetime.strptime(date_of_task,'%Y-%m-%d')
  date = date.strftime ('%d %m %Y')
  date = str(date)
  day_name= ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday','Sunday']
  day = datetime.strptime(date, '%d %m %Y'). weekday()
  return day_name[day]

@bp.route("/add", methods=["GET", "POST",])
def add_tasks():
    conn = db.get_db()
    cursor = conn.cursor()
    
    g.user_id = current_user.id if current_user.is_authenticated else None
    user_id = g.user_id
    if request.method == "GET":
        cursor.execute("select id,urgency from urgency")
        statuses = cursor.fetchall()
        today_date = datetime.today().strftime ('%Y-%m-%d')
        return render_template("add_task.html", statuses=statuses, today_date=today_date)
    elif request.method == "POST":
        task = request.form.get("task")
        date_of_task = request.form.get("date_of_task")
        urgency = request.form.get("urgency")
        points = request.form.get("points")
        status = 2
        day_of_task = day(date_of_task)
        cursor.execute("insert into task (task, date_of_task, day, points, urgency_id, status_id, user_id) values (%s,%s,%s,%s,%s,%s,%s)", (task, date_of_task, day_of_task, points, urgency, status, user_id))
        conn.commit()
        return redirect(url_for("index"), 302)
    
@bp.route("/<id>/detail")
def taskdetail(id):
    g.user_id = current_user.id if current_user.is_authenticated else None
    user_id = g.user_id
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("select t.task, t.date_of_task, u.urgency, t.points, ts.status from task t, urgency u, task_status ts where t.id = %s and u.id = t.urgency_id and t.status_id=ts.id and t.user_id=%s", (id, user_id))
    task = cursor.fetchone()
    if not task:
         return render_template("taskdetails.html"), 404 
    task, date_of_task, urgency, points, status = task
    id = int(id)
    status_colour = {"Completed" : "success",
                "Not Complete" : "dark"}
    urgency_colour = {"Normal": "primary",
               "Expendable" : "secondary",
               "Important" : "warning",
               "Very Important" : "danger"}

    return render_template("taskdetails.html", 
                           id = id,
                           task = task,
                           points = points,  
                           urgency=urgency,  
                           u_cls=urgency_colour[urgency],
                           s_cls=status_colour[status], 
                           status=status
                           )



@bp.route("/<id>/edit", methods=["GET", "POST",])
def edit_task(id): 
    g.user_id = current_user.id if current_user.is_authenticated else None
    user_id = g.user_id
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("select t.task, t.date_of_task, t.urgency_id, t.status_id, t.points from task t, urgency u where t.id = %s and u.id = t.urgency_id and t.user_id = %s", (id, user_id))
    task = cursor.fetchone()
    if not task:
        return render_template("taskdetails.html"), 404    

    if request.method == "GET":
        task, date_of_task, urgency, status, points = task
        cursor.execute("select id,urgency from urgency")
        statuses = cursor.fetchall()
        today_date = datetime.today().strftime ('%Y-%m-%d')
        return render_template("taskedit.html", 
                               id = id,
                               task=task,
                               date_of_task=date_of_task,
                               points=points,
                               urgency = urgency,
                               status=status,
                               statuses=statuses,
                               today_date=today_date
                               )
    elif request.method == "POST":
        task = request.form.get("task")
        date_of_task = request.form.get("date_of_task")
        points = request.form.get("points")
        urgency = request.form.get("urgency")
        status = request.form.get("status")
        if status not in ['1', '2']:
            status = '2'  # Default to 'Not Complete' if unexpected value
        day_of_task = day(date_of_task)  
        cursor.execute("update task set task = %s, date_of_task = %s, day=%s, status_id=%s, points=%s, urgency_id=%s where id=%s and user_id = %s", (task, date_of_task, day_of_task, status, points, urgency, id, user_id))
        conn.commit()
        return redirect(url_for("index"), 302)

@bp.route("/<id>/overdue")
def overdue(id):
    g.user_id = current_user.id if current_user.is_authenticated else None
    user_id = g.user_id
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("select o.task, o.points from overdue_tasks o where o.id = %s and o.user_id=%s", (id, user_id))
    overdue = cursor.fetchone()
    if not overdue:
         return render_template("overdue.html"), 404 
    task, points = overdue
    id = int(id)

    status_colour = {"Not Complete" : "dark"}
    overdue_colour = {"Overdue": "info"}

    return render_template("overdue.html", 
                           id = id,
                           task = task,
                           points = points,  
                           o_cls=overdue_colour["Overdue"],
                           s_cls=status_colour["Not Complete"]
                           )


@bp.route('/task/<id>/delete', methods=['GET', 'POST'])
def delete_task(id):
    g.user_id = current_user.id if current_user.is_authenticated else None
    user_id = g.user_id
    conn = db.get_db()
    cursor = conn.cursor()

    # Ensure the 'id' is an integer
    try:
        task_id = int(id)
    except ValueError:
        return render_template("error.html", message="Invalid task ID"), 400

    # Delete the task with the specified ID
    cursor.execute("DELETE FROM task WHERE id = %s and user_id = %s", (task_id, user_id))
    conn.commit()

    # Redirect to the index page after deletion
    return redirect(url_for('index'))


@bp.route("/filter", methods=['POST'])
def filter_tasks():
    data = request.get_json()
    title = data.get('title', '')
    start_date = data.get('startDate', '')
    end_date = data.get('endDate', '')
    urgencies = data.get('urgencies', [])

    conditions = []
    params = []

    if title:
        conditions.append("task ILIKE %s")
        params.append(f"%{title}%")
    if start_date:
        conditions.append("date_of_task >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("date_of_task <= %s")
        params.append(end_date)
    if urgencies:
        urgency_conditions = " OR ".join(["urgency_id = %s" for _ in urgencies])
        conditions.append(f"({urgency_conditions})")
        params.extend(urgencies)

    query = "SELECT id, task, date_of_task, day, urgency, status FROM task WHERE " + " AND ".join(conditions) if conditions else "1=1"

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    tasks = cursor.fetchall()
    cursor.close()

    tasks_list = [{'id': row[0], 'task': row[1], 'date_of_task': str(row[2]), 'day': row[3], 'urgency': row[4], 'status': row[5]} for row in tasks]
    return jsonify(tasks_list)

@bp.route('/complete_overdue_task/<int:id>', methods=['POST'])
def complete_overdue_task(id):
    # conn = db.get_db()
    # cursor = conn.cursor()

    # try:
    #     # First, fetch the task details from the overdue_tasks table
    #     cursor.execute("""
    #         SELECT task, date_of_task, day, points, urgency_id, user_id 
    #         FROM overdue_tasks 
    #         WHERE id = %s
    #     """, (id,))
    #     task_details = cursor.fetchone()

    #     if task_details:
    #         task, date_of_task, day, points, urgency_id, user_id = task_details

    #         # Check if the task completion checkbox was ticked
    #         if 'status' in request.form and request.form['status'] == '1':
    #             # Now insert the fetched data into the task table
                
    #             cursor.execute("""
    #                 INSERT INTO task (task, date_of_task, day, points, urgency_id, status_id, user_id) 
    #                 VALUES (%s, %s, %s, %s, %s, %s, %s)
    #             """, (task, date_of_task, day, points, urgency_id, '1', user_id))
                
    #             # Delete the task from overdue_tasks
    #             cursor.execute("DELETE FROM overdue_tasks WHERE id = %s", (id,))
    #             conn.commit()
    #     else:
    #         print("No task found with the provided ID.")

    # except Exception as e:
    #     conn.rollback()  # Rollback the transaction on error
    #     print(f'Error completing task: {str(e)}', 'error')

    # finally:
    #     cursor.close()
    #     conn.close()

    return redirect(url_for('index'))