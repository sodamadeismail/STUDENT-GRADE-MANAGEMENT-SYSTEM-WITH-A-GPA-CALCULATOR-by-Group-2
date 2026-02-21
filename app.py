from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "sirms_final_master_key_2026"

# --- Mock Database ---
# Note: In a real-world scenario, this would be a SQL database.
students = {
    "2024/001": {
        "name": "Alice Johnson",
        "pw": "123",
        "level": "200L",
        "dept": "Computer Science",
        "results": {
            "100L": [
                {"course": "CSC101", "units": 3, "score": 75.0, "point": 5.0, "grade": "A"},
                {"course": "MTH101", "units": 4, "score": 62.0, "point": 4.0, "grade": "B"}
            ]
        }
    }
}
admin_pass = "admin123"

# --- Utility Functions ---

def calculate_grade(score):
    """Converts a raw numeric score to Grade Points and Letter Grades."""
    if score >= 70: return 5.0, "A"
    elif score >= 60: return 4.0, "B"
    elif score >= 50: return 3.0, "C"
    elif score >= 45: return 2.0, "D"
    elif score >= 40: return 1.0, "E"
    else: return 0.0, "F"

# --- Authentication Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    username = request.form.get('username').upper()
    password = request.form.get('password')

    if role == 'admin':
        if password == admin_pass:
            session['user'] = 'admin'
            return redirect(url_for('admin_dashboard'))
    else:
        if username in students and students[username]['pw'] == password:
            session['user'] = username
            return redirect(url_for('student_dashboard'))
    
    flash("Invalid Identification or Password!")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- Student Routes ---

@app.route('/student_dashboard')
def student_dashboard():
    user_id = session.get('user')
    if not user_id or user_id == 'admin': 
        return redirect(url_for('home'))
    
    data = students[user_id]
    levels, level_gpas = [], []
    total_gp, total_u = 0, 0

    # Sort results to ensure the graph plots chronologically
    for lvl in sorted(data['results'].keys()):
        courses = data['results'][lvl]
        if courses:
            l_gp = sum(c['units'] * c['point'] for c in courses)
            l_u = sum(c['units'] for c in courses)
            gpa = round(l_gp / l_u, 2) if l_u > 0 else 0
            
            levels.append(lvl)
            level_gpas.append(gpa)
            total_gp += l_gp
            total_u += l_u

    cgpa = round(total_gp / total_u, 2) if total_u > 0 else 0.0
    return render_template('student.html', data=data, cgpa=cgpa, levels=levels, level_gpas=level_gpas)

# --- Admin Management Routes ---

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('user') != 'admin': 
        return redirect(url_for('home'))
    return render_template('admin.html', student_list=students)

@app.route('/manage/<path:matric>')
def manage_student(matric):
    """The route that powers the 'View' button to see/delete student records."""
    if session.get('user') != 'admin': 
        return redirect(url_for('home'))
    if matric in students:
        return render_template('manage_student.html', matric=matric, info=students[matric])
    flash("Student not found!")
    return redirect(url_for('admin_dashboard'))

@app.route('/add_student', methods=['POST'])
def add_student():
    if session.get('user') == 'admin':
        matric = request.form.get('matric').upper()
        level = request.form.get('level')
        if matric not in students:
            students[matric] = {
                "name": request.form.get('name'), 
                "pw": "123",
                "level": level, 
                "dept": request.form.get('dept'),
                "results": {level: []}
            }
            flash(f"Success: Registered {matric} at {level}.")
        else:
            flash("Error: Student already exists.")
    return redirect(url_for('admin_dashboard'))

@app.route('/upload_grade', methods=['POST'])
def upload_grade():
    if session.get('user') == 'admin':
        matric = request.form.get('matric').upper()
        if matric in students:
            score = float(request.form.get('score'))
            gp, letter = calculate_grade(score)
            target_lvl = request.form.get('target_level')
            
            if target_lvl not in students[matric]['results']:
                students[matric]['results'][target_lvl] = []
            
            students[matric]['results'][target_lvl].append({
                "course": request.form.get('course').upper(),
                "units": int(request.form.get('units')),
                "score": score, 
                "point": gp, 
                "grade": letter
            })
            flash(f"Result uploaded for {matric} ({target_lvl})")
        else:
            flash("Student Matric Number not found.")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_student/<matric>')
def delete_student(matric):
    """Permanently removes a student from the mock database."""
    if session.get('user') == 'admin' and matric in students:
        del students[matric]
        flash(f"Student {matric} deleted successfully.")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_course/<matric>/<level>/<int:index>')
def delete_course(matric, level, index):
    """Deletes a specific course entry within a student's level."""
    if session.get('user') == 'admin' and matric in students:
        if level in students[matric]['results']:
            students[matric]['results'][level].pop(index)
            flash("Course entry removed.")
    return redirect(url_for('manage_student', matric=matric))

if __name__ == "__main__":
    app.run(debug=True)