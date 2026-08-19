from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    flash,
    render_template_string,
    send_file
)

import sqlite3
from datetime import datetime
from functools import wraps
import os


# =========================================================
# APP CONFIG
# =========================================================

app = Flask(__name__)

app.secret_key = "smarthire_secret_key_2026"

DATABASE = "smarthire.db"

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db_connection()

    cursor = conn.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT DEFAULT 'candidate'

        )
    """)


    # JOBS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            company TEXT NOT NULL,

            location TEXT NOT NULL,

            job_type TEXT NOT NULL,

            salary TEXT,

            description TEXT,

            requirements TEXT,

            status TEXT DEFAULT 'Active',

            created_date TEXT NOT NULL

        )
    """)


    # APPLICATIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            email TEXT NOT NULL,

            phone TEXT NOT NULL,

            applied_date TEXT NOT NULL,

            applied_time TEXT NOT NULL,

            status TEXT DEFAULT 'Applied'

        )
    """)


    # RESUME
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            file_name TEXT,

            file_path TEXT,

            uploaded_at TEXT

        )
    """)


    # =====================================================
    # RESUME MIGRATION
    # =====================================================

    cursor.execute("PRAGMA table_info(resume)")

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]


    if "user_id" not in columns:

        cursor.execute(
            "ALTER TABLE resume ADD COLUMN user_id INTEGER"
        )


    if "file_name" not in columns:

        cursor.execute(
            "ALTER TABLE resume ADD COLUMN file_name TEXT"
        )


    if "file_path" not in columns:

        cursor.execute(
            "ALTER TABLE resume ADD COLUMN file_path TEXT"
        )


    if "uploaded_at" not in columns:

        cursor.execute(
            "ALTER TABLE resume ADD COLUMN uploaded_at TEXT"
        )


    # =====================================================
    # ADMIN USER
    # =====================================================

    admin = cursor.execute("""
        SELECT id
        FROM users
        WHERE email=?
    """, (
        "admin@smarthire.com",
    )).fetchone()


    if admin is None:

        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )
            VALUES (?, ?, ?, ?)
        """, (
            "Admin",
            "admin@smarthire.com",
            "admin123",
            "admin"
        ))


    # =====================================================
    # STUDENT USER
    # =====================================================

    student = cursor.execute("""
        SELECT id
        FROM users
        WHERE email=?
    """, (
        "student@smarthire.com",
    )).fetchone()


    if student is None:

        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )
            VALUES (?, ?, ?, ?)
        """, (
            "Student",
            "student@smarthire.com",
            "student123",
            "candidate"
        ))


    # =====================================================
    # SAMPLE JOBS
    # =====================================================

    job_count = cursor.execute("""
        SELECT COUNT(*)
        FROM jobs
    """).fetchone()[0]


    if job_count == 0:

        today = datetime.now().strftime("%Y-%m-%d")


        jobs = [

            (
                "Software Developer",
                "TCS",
                "Chennai",
                "Full Time",
                "₹4 - ₹6 LPA",
                "Develop and maintain software applications.",
                "Python, Java, SQL, Problem Solving",
                "Active",
                today
            ),

            (
                "Data Analyst",
                "Infosys",
                "Bangalore",
                "Full Time",
                "₹5 - ₹8 LPA",
                "Analyze business data and prepare reports.",
                "Excel, SQL, Power BI, Communication",
                "Active",
                today
            ),

            (
                "Web Developer",
                "Zoho",
                "Chennai",
                "Full Time",
                "₹4 - ₹7 LPA",
                "Build responsive web applications.",
                "HTML, CSS, JavaScript, Python",
                "Active",
                today
            ),

            (
                "Business Analyst",
                "Accenture",
                "Hyderabad",
                "Full Time",
                "₹5 - ₹9 LPA",
                "Analyze business requirements and solutions.",
                "Excel, SQL, Communication, Analytics",
                "Active",
                today
            ),

            (
                "Junior Accountant",
                "Deloitte",
                "Mumbai",
                "Full Time",
                "₹3 - ₹5 LPA",
                "Support accounting and financial reporting.",
                "Tally, Excel, Accounting, GST",
                "Active",
                today
            )
        ]


        cursor.executemany("""
            INSERT INTO jobs
            (
                title,
                company,
                location,
                job_type,
                salary,
                description,
                requirements,
                status,
                created_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, jobs)


    conn.commit()

    conn.close()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# ADMIN REQUIRED
# =========================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )


        if session.get("role") != "admin":

            flash(
                "Admin access required.",
                "error"
            )

            return redirect(
                url_for("jobs")
            )


        return function(*args, **kwargs)

    return wrapper


# =========================================================
# STYLE
# =========================================================

BASE_STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #f4f7fb;

    color: #172554;
}

.navbar {

    min-height: 75px;

    background:
        linear-gradient(
            135deg,
            #111936,
            #30358c
        );

    color: white;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 15px 5%;

}

.logo {

    font-size: 27px;

    font-weight: 800;

}

.nav-right {

    display: flex;

    align-items: center;

    gap: 10px;

    flex-wrap: wrap;

}

.container {

    width: 92%;

    max-width: 1400px;

    margin: 40px auto;

}

.hero {

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 20px;

    margin-bottom: 30px;

}

.hero h1 {

    font-size: 38px;

    margin: 0 0 10px;

}

.hero p {

    color: #64748b;

}

.cards {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 20px;

    margin-bottom: 30px;

}

.card {

    background: white;

    border-radius: 18px;

    padding: 25px;

    box-shadow:
        0 8px 30px
        rgba(15,23,42,.07);

}

.panel {

    background: white;

    border-radius: 18px;

    padding: 25px;

    margin-bottom: 25px;

    box-shadow:
        0 8px 30px
        rgba(15,23,42,.06);

}

.stat-title {

    color: #64748b;

    font-weight: 700;

}

.stat-number {

    font-size: 36px;

    font-weight: 800;

    margin-top: 15px;

}

.btn {

    border: none;

    padding: 11px 18px;

    border-radius: 10px;

    cursor: pointer;

    text-decoration: none;

    display: inline-block;

    font-weight: 700;

}

.btn-primary {

    background: #2563eb;

    color: white;

}

.btn-success {

    background: #16a34a;

    color: white;

}

.btn-danger {

    background: #ef4444;

    color: white;

}

.btn-warning {

    background: #f59e0b;

    color: white;

}

.btn-light {

    background: #e8eefb;

    color: #172554;

}

.btn-small {

    padding: 7px 11px;

    font-size: 13px;

}

table {

    width: 100%;

    border-collapse: collapse;

}

th {

    background: #f8fafc;

    padding: 14px;

    text-align: left;

}

td {

    padding: 14px;

    border-bottom:
        1px solid #edf1f7;

}

.form-card {

    max-width: 850px;

    margin: auto;

}

.form-group {

    margin-bottom: 18px;

}

.form-label {

    display: block;

    font-weight: 700;

    margin-bottom: 7px;

}

.form-input,
.form-select,
.form-textarea {

    width: 100%;

    padding: 13px;

    border:
        1px solid #d5ddea;

    border-radius: 10px;

    font-size: 15px;

}

.form-textarea {

    min-height: 130px;

}

.form-grid {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 18px;

}

.full {

    grid-column: 1 / -1;

}

.flash {

    padding: 14px 18px;

    border-radius: 10px;

    margin-bottom: 18px;

    font-weight: 700;

}

.flash-success {

    background: #dcfce7;

    color: #166534;

}

.flash-error {

    background: #fee2e2;

    color: #991b1b;

}

.badge {

    padding: 7px 12px;

    border-radius: 20px;

    font-size: 12px;

    font-weight: 700;

}

.badge-applied {

    background: #dbeafe;

    color: #1d4ed8;

}

.badge-review {

    background: #fef3c7;

    color: #b45309;

}

.badge-selected {

    background: #dcfce7;

    color: #15803d;

}

.badge-rejected {

    background: #fee2e2;

    color: #b91c1c;

}

.badge-active {

    background: #dcfce7;

    color: #15803d;

}

.login-page {

    min-height: 100vh;

    display: flex;

    align-items: center;

    justify-content: center;

    background:
        linear-gradient(
            135deg,
            #111936,
            #30358c
        );

}

.login-card {

    width: 430px;

    background: white;

    padding: 40px;

    border-radius: 22px;

}

.empty {

    text-align: center;

    padding: 40px;

    color: #64748b;

}

@media(max-width: 900px) {

    .cards {

        grid-template-columns:
            1fr 1fr;

    }

    .form-grid {

        grid-template-columns:
            1fr;

    }

    .full {

        grid-column: auto;

    }

}

@media(max-width: 600px) {

    .cards {

        grid-template-columns:
            1fr;

    }

    .hero {

        flex-direction: column;

        align-items: flex-start;

    }

}

</style>
"""


# =========================================================
# NAVBAR
# =========================================================

def navbar():

    if "user_id" not in session:

        return ""

    name = session.get(
        "name",
        "User"
    )


    admin_button = ""

    if session.get("role") == "admin":

        admin_button = """
        <a
            href="/admin-dashboard"
            class="btn btn-warning"
        >
            Admin Dashboard
        </a>
        """


    return f"""
    <div class="navbar">

        <div class="logo">
            🤖 SmartHire
        </div>

        <div class="nav-right">

            <span>
                Welcome, {name}
            </span>

            <a
                href="/jobs"
                class="btn btn-light"
            >
                Jobs
            </a>

            <a
                href="/applications"
                class="btn btn-light"
            >
                Applications
            </a>

            <a
                href="/resume"
                class="btn btn-light"
            >
                CV / Resume
            </a>

            {admin_button}

            <a
                href="/logout"
                class="btn btn-danger"
            >
                Logout
            </a>

        </div>

    </div>
    """


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" in session:

        return redirect(
            url_for("jobs")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        conn = get_db_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email=?
            AND password=?
        """, (
            email,
            password
        )).fetchone()

        conn.close()


        if user:

            session["user_id"] = user["id"]

            session["name"] = user["name"]

            session["email"] = user["email"]

            session["role"] = user["role"]


            flash(
                "Login successful!",
                "success"
            )


            if user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(
                url_for("jobs")
            )


        flash(
            "Invalid email or password.",
            "error"
        )


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            SmartHire Login
        </title>

        {BASE_STYLE}

    </head>

    <body>

        <div class="login-page">

            <div class="login-card">

                <div style="
                    text-align:center;
                    font-size:50px;
                ">
                    🤖
                </div>

                <h1 style="
                    text-align:center;
                ">
                    SmartHire
                </h1>

                <p style="
                    text-align:center;
                    color:#64748b;
                ">
                    AI Placement & Interview Management System
                </p>


                {{% with messages =
                    get_flashed_messages(
                        with_categories=true
                    )
                %}}

                    {{% for category, message in messages %}}

                        <div class="flash flash-{{{{ category }}}}">

                            {{{{ message }}}}

                        </div>

                    {{% endfor %}}

                {{% endwith %}}


                <form method="POST">

                    <div class="form-group">

                        <label class="form-label">
                            Email
                        </label>

                        <input
                            type="email"
                            name="email"
                            class="form-input"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Password
                        </label>

                        <input
                            type="password"
                            name="password"
                            class="form-input"
                            required
                        >

                    </div>


                    <button
                        type="submit"
                        class="btn btn-primary"
                        style="width:100%;"
                    >
                        Login
                    </button>

                </form>


                <div style="
                    background:#f1f5f9;
                    padding:15px;
                    border-radius:10px;
                    margin-top:20px;
                    font-size:13px;
                ">

                    <b>Admin Login</b><br>

                    admin@smarthire.com<br>

                    admin123

                    <br><br>

                    <b>Student Login</b><br>

                    student@smarthire.com<br>

                    student123

                </div>

            </div>

        </div>

    </body>

    </html>
    """

    return render_template_string(html)


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# JOBS
# =========================================================

@app.route("/jobs")
@login_required
def jobs():

    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = get_db_connection()


    if search:

        keyword = "%" + search + "%"

        jobs_list = conn.execute("""
            SELECT *
            FROM jobs
            WHERE
                title LIKE ?
                OR company LIKE ?
                OR location LIKE ?
            ORDER BY id DESC
        """, (
            keyword,
            keyword,
            keyword
        )).fetchall()

    else:

        jobs_list = conn.execute("""
            SELECT *
            FROM jobs
            ORDER BY id DESC
        """).fetchall()


    total_jobs = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
    """).fetchone()[0]


    active_jobs = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE status='Active'
    """).fetchone()[0]


    total_applications = conn.execute("""
        SELECT COUNT(*)
        FROM applications
    """).fetchone()[0]


    total_companies = conn.execute("""
        SELECT COUNT(DISTINCT company)
        FROM jobs
    """).fetchone()[0]


    conn.close()


    rows = ""


    for job in jobs_list:

        admin_actions = ""


        if session.get("role") == "admin":

            admin_actions = f"""
            <a
                href="/jobs/edit/{job["id"]}"
                class="btn btn-small btn-warning"
            >
                Edit
            </a>

            <a
                href="/jobs/delete/{job["id"]}"
                class="btn btn-small btn-danger"
                onclick="return confirm('Delete this job?')"
            >
                Delete
            </a>
            """


        rows += f"""
        <tr>

            <td>
                <b>{job["title"]}</b>
            </td>

            <td>
                {job["company"]}
            </td>

            <td>
                {job["location"]}
            </td>

            <td>
                {job["job_type"]}
            </td>

            <td>
                {job["salary"]}
            </td>

            <td>

                <span class="badge badge-active">

                    {job["status"]}

                </span>

            </td>

            <td>

                <a
                    href="/job/{job["id"]}"
                    class="btn btn-small btn-light"
                >
                    View
                </a>

                {admin_actions}

            </td>

        </tr>
        """


    if not rows:

        rows = """
        <tr>

            <td colspan="7">

                <div class="empty">

                    No jobs found.

                </div>

            </td>

        </tr>
        """


    add_job_button = ""


    if session.get("role") == "admin":

        add_job_button = """
        <a
            href="/jobs/add"
            class="btn btn-primary"
        >
            + Add Job
        </a>
        """


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            SmartHire Jobs
        </title>

        {BASE_STYLE}

    </head>

    <body>

        {navbar()}

        <div class="container">


            {{% with messages =
                get_flashed_messages(
                    with_categories=true
                )
            %}}

                {{% for category, message in messages %}}

                    <div class="flash flash-{{{{ category }}}}">

                        {{{{ message }}}}

                    </div>

                {{% endfor %}}

            {{% endwith %}}


            <div class="hero">

                <div>

                    <h1>
                        Job Management
                    </h1>

                    <p>
                        Find and manage placement opportunities.
                    </p>

                </div>

                {add_job_button}

            </div>


            <div class="cards">

                <div class="card">

                    <div class="stat-title">
                        Total Jobs
                    </div>

                    <div class="stat-number">
                        {total_jobs}
                    </div>

                </div>


                <div class="card">

                    <div class="stat-title">
                        Active Jobs
                    </div>

                    <div class="stat-number">
                        {active_jobs}
                    </div>

                </div>


                <div class="card">

                    <div class="stat-title">
                        Applications
                    </div>

                    <div class="stat-number">
                        {total_applications}
                    </div>

                </div>


                <div class="card">

                    <div class="stat-title">
                        Companies
                    </div>

                    <div class="stat-number">
                        {total_companies}
                    </div>

                </div>

            </div>


            <div class="panel">

                <form method="GET">

                    <input
                        type="text"
                        name="search"
                        class="form-input"
                        placeholder="Search job, company or location"
                        value="{search}"
                    >

                    <br><br>

                    <button
                        type="submit"
                        class="btn btn-primary"
                    >
                        Search
                    </button>

                </form>

            </div>


            <div class="panel">

                <h2>
                    Available Opportunities
                </h2>

                <div style="
                    overflow-x:auto;
                ">

                    <table>

                        <thead>

                            <tr>

                                <th>Job</th>

                                <th>Company</th>

                                <th>Location</th>

                                <th>Type</th>

                                <th>Salary</th>

                                <th>Status</th>

                                <th>Actions</th>

                            </tr>

                        </thead>

                        <tbody>

                            {rows}

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

    </body>

    </html>
    """

    return render_template_string(html)


# =========================================================
# ADD JOB
# =========================================================

@app.route(
    "/jobs/add",
    methods=["GET", "POST"]
)
@admin_required
def add_job():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        company = request.form.get(
            "company",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        job_type = request.form.get(
            "job_type",
            "Full Time"
        ).strip()

        salary = request.form.get(
            "salary",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        requirements = request.form.get(
            "requirements",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Active"
        )


        if not title or not company or not location:

            flash(
                "Please fill required fields.",
                "error"
            )

            return redirect(
                url_for("add_job")
            )


        conn = get_db_connection()


        conn.execute("""
            INSERT INTO jobs
            (
                title,
                company,
                location,
                job_type,
                salary,
                description,
                requirements,
                status,
                created_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            company,
            location,
            job_type,
            salary,
            description,
            requirements,
            status,
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        ))


        conn.commit()

        conn.close()


        flash(
            "Job added successfully!",
            "success"
        )


        return redirect(
            url_for("jobs")
        )


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            Add Job
        </title>

        {BASE_STYLE}

    </head>

    <body>

        {navbar()}

        <div class="container">

            <div class="hero">

                <h1>
                    Add New Job
                </h1>

                <a
                    href="/jobs"
                    class="btn btn-light"
                >
                    Back
                </a>

            </div>


            <div class="card form-card">

                <form method="POST">

                    <div class="form-grid">


                        <div class="form-group">

                            <label class="form-label">
                                Job Title *
                            </label>

                            <input
                                name="title"
                                class="form-input"
                                required
                            >

                        </div>


                        <div class="form-group">

                            <label class="form-label">
                                Company *
                            </label>

                            <input
                                name="company"
                                class="form-input"
                                required
                            >

                        </div>


                        <div class="form-group">

                            <label class="form-label">
                                Location *
                            </label>

                            <input
                                name="location"
                                class="form-input"
                                required
                            >

                        </div>


                        <div class="form-group">

                            <label class="form-label">
                                Job Type
                            </label>

                            <select
                                name="job_type"
                                class="form-select"
                            >

                                <option>
                                    Full Time
                                </option>

                                <option>
                                    Part Time
                                </option>

                                <option>
                                    Internship
                                </option>

                                <option>
                                    Remote
                                </option>

                            </select>

                        </div>


                        <div class="form-group">

                            <label class="form-label">
                                Salary
                            </label>

                            <input
                                name="salary"
                                class="form-input"
                                placeholder="₹4 - ₹6 LPA"
                            >

                        </div>


                        <div class="form-group">

                            <label class="form-label">
                                Status
                            </label>

                            <select
                                name="status"
                                class="form-select"
                            >

                                <option>
                                    Active
                                </option>

                                <option>
                                    Closed
                                </option>

                            </select>

                        </div>


                        <div class="form-group full">

                            <label class="form-label">
                                Job Description
                            </label>

                            <textarea
                                name="description"
                                class="form-textarea"
                            ></textarea>

                        </div>


                        <div class="form-group full">

                            <label class="form-label">
                                Requirements
                            </label>

                            <textarea
                                name="requirements"
                                class="form-textarea"
                                placeholder="Python, SQL, Excel, Communication..."
                            ></textarea>

                        </div>


                    </div>


                    <button
                        type="submit"
                        class="btn btn-primary"
                    >
                        Create Job
                    </button>


                    <a
                        href="/jobs"
                        class="btn btn-light"
                    >
                        Cancel
                    </a>

                </form>

            </div>

        </div>

    </body>

    </html>
    """

    return render_template_string(html)


# =========================================================
# EDIT JOB
# =========================================================

@app.route(
    "/jobs/edit/<int:job_id>",
    methods=["GET", "POST"]
)
@admin_required
def edit_job(job_id):

    conn = get_db_connection()


    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id=?
    """, (
        job_id,
    )).fetchone()


    if not job:

        conn.close()

        flash(
            "Job not found.",
            "error"
        )

        return redirect(
            url_for("jobs")
        )


    if request.method == "POST":

        conn.execute("""
            UPDATE jobs

            SET
                title=?,
                company=?,
                location=?,
                job_type=?,
                salary=?,
                description=?,
                requirements=?,
                status=?

            WHERE id=?
        """, (
            request.form.get(
                "title",
                ""
            ),

            request.form.get(
                "company",
                ""
            ),

            request.form.get(
                "location",
                ""
            ),

            request.form.get(
                "job_type",
                ""
            ),

            request.form.get(
                "salary",
                ""
            ),

            request.form.get(
                "description",
                ""
            ),

            request.form.get(
                "requirements",
                ""
            ),

            request.form.get(
                "status",
                "Active"
            ),

            job_id
        ))


        conn.commit()

        conn.close()


        flash(
            "Job updated successfully!",
            "success"
        )


        return redirect(
            url_for("jobs")
        )


    conn.close()


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            Edit Job
        </title>

        {BASE_STYLE}

    </head>

    <body>

        {navbar()}

        <div class="container">

            <div class="hero">

                <h1>
                    Edit Job
                </h1>

                <a
                    href="/jobs"
                    class="btn btn-light"
                >
                    Back
                </a>

            </div>


            <div class="card form-card">

                <form method="POST">


                    <div class="form-group">

                        <label class="form-label">
                            Job Title
                        </label>

                        <input
                            name="title"
                            class="form-input"
                            value="{job["title"]}"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Company
                        </label>

                        <input
                            name="company"
                            class="form-input"
                            value="{job["company"]}"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Location
                        </label>

                        <input
                            name="location"
                            class="form-input"
                            value="{job["location"]}"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Job Type
                        </label>

                        <input
                            name="job_type"
                            class="form-input"
                            value="{job["job_type"]}"
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Salary
                        </label>

                        <input
                            name="salary"
                            class="form-input"
                            value="{job["salary"] or ""}"
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Status
                        </label>

                        <select
                            name="status"
                            class="form-select"
                        >

                            <option
                                {"selected" if job["status"] == "Active" else ""}
                            >
                                Active
                            </option>

                            <option
                                {"selected" if job["status"] == "Closed" else ""}
                            >
                                Closed
                            </option>

                        </select>

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Job Description
                        </label>

                        <textarea
                            name="description"
                            class="form-textarea"
                        >{job["description"] or ""}</textarea>

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Requirements
                        </label>

                        <textarea
                            name="requirements"
                            class="form-textarea"
                        >{job["requirements"] or ""}</textarea>

                    </div>


                    <button
                        type="submit"
                        class="btn btn-primary"
                    >
                        Save Changes
                    </button>


                </form>

            </div>

        </div>

    </body>

    </html>
    """

    return render_template_string(html)


# =========================================================
# DELETE JOB
# =========================================================

@app.route(
    "/jobs/delete/<int:job_id>"
)
@admin_required
def delete_job(job_id):

    conn = get_db_connection()


    conn.execute("""
        DELETE FROM applications
        WHERE job_id=?
    """, (
        job_id,
    ))


    conn.execute("""
        DELETE FROM jobs
        WHERE id=?
    """, (
        job_id,
    ))


    conn.commit()

    conn.close()


    flash(
        "Job deleted successfully!",
        "success"
    )


    return redirect(
        url_for("jobs")
    )


# =========================================================
# JOB DETAILS
# =========================================================

@app.route(
    "/job/<int:job_id>"
)
@login_required
def job_details(job_id):

    conn = get_db_connection()


    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id=?
    """, (
        job_id,
    )).fetchone()


    conn.close()


    if not job:

        flash(
            "Job not found.",
            "error"
        )

        return redirect(
            url_for("jobs")
        )


    apply_button = ""


    if job["status"] == "Active":

        apply_button = f"""
        <a
            href="/apply/{job_id}"
            class="btn btn-primary"
        >
            Apply Now
        </a>
        """

    else:

        apply_button = """
        <span class="badge badge-rejected">
            Applications Closed
        </span>
        """


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            {job["title"]}
        </title>

        {BASE_STYLE}

    </head>

    <body>

        {navbar()}


        <div class="container">


            <div class="hero">

                <div>

                    <h1>
                        {job["title"]}
                    </h1>

                    <p>
                        {job["company"]}
                        •
                        {job["location"]}
                    </p>

                </div>


                <a
                    href="/jobs"
                    class="btn btn-light"
                >
                    Back
                </a>

            </div>


            <div class="card">

                <h2>
                    About the Role
                </h2>

                <p style="
                    line-height:1.8;
                ">
                    {job["description"] or "No description provided."}
                </p>


                <h2>
                    Requirements
                </h2>

                <p style="
                    line-height:1.8;
                ">
                    {job["requirements"] or "No requirements specified."}
                </p>


                <br>

                {apply_button}

            </div>

        </div>

    </body>

    </html>
    """

    return render_template_string(html)


# =========================================================
# APPLY JOB
# =========================================================

@app.route(
    "/apply/<int:job_id>",
    methods=["GET", "POST"]
)
@login_required
def apply_job(job_id):

    conn = get_db_connection()


    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id=?
    """, (
        job_id,
    )).fetchone()


    if not job:

        conn.close()

        flash(
            "Job not found.",
            "error"
        )

        return redirect(
            url_for("jobs")
        )


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()


        if not name or not email or not phone:

            conn.close()

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(
                url_for(
                    "apply_job",
                    job_id=job_id
                )
            )


        existing = conn.execute("""
            SELECT id
            FROM applications
            WHERE job_id=?
            AND user_id=?
        """, (
            job_id,
            session["user_id"]
        )).fetchone()


        if existing:

            conn.close()

            flash(
                "You have already applied for this job.",
                "error"
            )

            return redirect(
                url_for("applications")
            )


        now = datetime.now()


        conn.execute("""
            INSERT INTO applications
            (
                job_id,
                user_id,
                name,
                email,
                phone,
                applied_date,
                applied_time,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            session["user_id"],
            name,
            email,
            phone,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            "Applied"
        ))


        conn.commit()

        conn.close()


        flash(
            "Application submitted successfully!",
            "success"
        )


        return redirect(
            url_for("applications")
        )


    conn.close()


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            Apply - SmartHire
        </title>

        {BASE_STYLE}

    </head>

    <body>

        {navbar()}


        <div class="container">

            <div class="hero">

                <div>

                    <h1>
                        Apply for Job
                    </h1>

                    <p>
                        {job["title"]}
                        at
                        {job["company"]}
                    </p>

                </div>

            </div>


            <div class="card form-card">


                {{% with messages =
                    get_flashed_messages(
                        with_categories=true
                    )
                %}}

                    {{% for category, message in messages %}}

                        <div class="flash flash-{{{{ category }}}}">

                            {{{{ message }}}}

                        </div>

                    {{% endfor %}}

                {{% endwith %}}


                <form method="POST">


                    <div class="form-group">

                        <label class="form-label">
                            Full Name
                        </label>

                        <input
                            name="name"
                            class="form-input"
                            value="{session.get("name", "")}"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Email
                        </label>

                        <input
                            type="email"
                            name="email"
                            class="form-input"
                            value="{session.get("email", "")}"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label class="form-label">
                            Phone
                        </label>

                        <input
                            name="phone"
                            class="form-input"
                            required
                        >

                    </div>


                    <button
                        type="submit"
                        class="btn btn-primary"
                    >
                        Submit Application
                    </button>


                    <a
                        href="/jobs"
                        class="btn btn-light"
                    >
                        Cancel
                    </a>


                </form>

            </div>

        </div>

    </body>

    </html>
    """

    return render_template_string(html)


# =========================================================
# APPLICATIONS
# =========================================================

@app.route("/applications")
@login_required
def applications():

    conn = get_db_connection()


    if session.get("role") == "admin":

        applications_list = conn.execute("""
            SELECT
                applications.*,
                jobs.title,
                jobs.company
            FROM applications
            JOIN jobs
            ON applications.job_id = jobs.id
            ORDER BY applications.id DESC
        """).fetchall()

    else:

        applications_list = conn.execute("""
            SELECT
                applications.*,
                jobs.title,
                jobs.company
            FROM applications
            JOIN jobs
            ON applications.job_id = jobs.id
            WHERE applications.user_id=?
            ORDER BY applications.id DESC
        """, (
            session["user_id"],
        )).fetchall()


    conn.close()


    rows = ""


    for application in applications_list:

        status = application["status"]


        if status == "Applied":

            badge = "badge-applied"

        elif status == "Under Review":

            badge = "badge-review"

        elif status == "Selected":

            badge = "badge-selected"

        else:

            badge = "badge-rejected"


        admin_action = ""


        if session.get("role") == "admin":

            admin_action = f"""
            <form
                method="POST"
                action="/applications/status/{application["id"]}"
            >

                <select
                    name="status"
                    class="form-select"
                    onchange="this.form.submit()"
                >

                    <option
                        value="Applied"
                        {"selected" if status == "Applied" else ""}
                    >
                        Applied
                    </option>


                    <option
                        value="Under Review"
                        {"selected" if status == "Under Review" else ""}
                    >
                        Under Review
                    </option>


                    <option
                        value="Selected"
                        {"selected" if status == "Selected" else ""}
                    >
                        Selected
                    </option>


                    <option
                        value="Rejected"
                        {"selected" if status == "Rejected" else ""}
                    >
                        Rejected
                    </option>

                </select>

            </form>
            """


        rows += f"""
        <tr>

            <td>
                <b>
                    {application["title"]}
                </b>
            </td>

            <td>
                {application["company"]}
            </td>

            <td>
                {application["name"]}
            </td>

            <td>
                {application["email"]}
            </td>

            <td>
                {application["phone"]}
            </td>

            <td>

                {application["applied_date"]}

                <br>

                {application["applied_time"]}

            </td>

            <td>

                <span
                    class="badge {badge}"
                >
                    {status}
                </span>

            </td>

            <td>

                {admin_action}

            </td>

        </tr>
        """


    if not rows:

        rows = """
        <tr>

            <td colspan="8">

                <div class="empty">

                    No applications found.

                </div>

            </td>

        </tr>
        """


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            Applications
        </title>

        {BASE_STYLE}

    </head>

    <body>

        {navbar()}


        <div class="container">


            <div class="hero">

                <div>

                    <h1>
                        Applications
                    </h1>

                    <p>
                        Track candidate applications and status.
                    </p>

                </div>

            </div>


            {{% with messages =
                get_flashed_messages(
                    with_categories=true
                )
            %}}

                {{% for category, message in messages %}}

                    <div class="flash flash-{{{{ category }}}}">

                        {{{{ message }}}}

                    </div>

                {{% endfor %}}

            {{% endwith %}}


            <div class="panel">

                <div style="
                    overflow-x:auto;
                ">

                    <table>

                        <thead>

                            <tr>

                                <th>Job</th>

                                <th>Company</th>

                                <th>Candidate</th>

                                <th>Email</th>

                                <th>Phone</th>

                                <th>Applied On</th>

                                <th>Status</th>

                                <th>Action</th>

                            </tr>

                        </thead>


                        <tbody>

                            {rows}

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

    </body>

    </html>
    """

    return render_template_string(html)


# =========================================================
# UPDATE APPLICATION STATUS
# =========================================================

@app.route(
    "/applications/status/<int:application_id>",
    methods=["POST"]
)
@admin_required
def update_application_status(
    application_id
):

    new_status = request.form.get(
        "status",
        "Applied"
    )


    allowed_statuses = [
        "Applied",
        "Under Review",
        "Selected",
        "Rejected"
    ]


    if new_status not in allowed_statuses:

        flash(
            "Invalid application status.",
            "error"
        )

        return redirect(
            url_for("applications")
        )


    conn = get_db_connection()


    application = conn.execute("""
        SELECT id
        FROM applications
        WHERE id=?
    """, (
        application_id,
    )).fetchone()


    if not application:

        conn.close()

        flash(
            "Application not found.",
            "error"
        )

        return redirect(
            url_for("applications")
        )


    conn.execute("""
        UPDATE applications
        SET status=?
        WHERE id=?
    """, (
        new_status,
        application_id
    ))


    conn.commit()

    conn.close()


    flash(
        "Application status updated successfully!",
        "success"
    )


    return redirect(
        url_for("applications")
    )


# =========================================================
# RESUME / CV UPLOAD
# =========================================================

@app.route(
    "/resume",
    methods=["GET", "POST"]
)
@login_required
def resume():

    # -----------------------------------------------------
    # UPLOAD
    # -----------------------------------------------------

    if request.method == "POST":

        file = request.files.get(
            "resume"
        )


        if file is None or file.filename == "":

            flash(
                "Please select a CV file.",
                "error"
            )

            return redirect(
                url_for("resume")
            )


        allowed_extensions = {
            "pdf",
            "doc",
            "docx"
        }


        if "." not in file.filename:

            flash(
                "Invalid CV file.",
                "error"
            )

            return redirect(
                url_for("resume")
            )


        extension = file.filename.rsplit(
            ".",
            1
        )[1].lower()


        if extension not in allowed_extensions:

            flash(
                "Only PDF, DOC and DOCX files are allowed.",
                "error"
            )

            return redirect(
                url_for("resume")
            )


        original_name = file.filename


        safe_name = (
            str(session["user_id"])
            + "_"
            + original_name.replace(
                " ",
                "_"
            )
        )


        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            safe_name
        )


        file.save(file_path)


        conn = get_db_connection()


        existing = conn.execute("""
            SELECT id
            FROM resume
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 1
        """, (
            session["user_id"],
        )).fetchone()


        uploaded_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        if existing:

            conn.execute("""
                UPDATE resume

                SET
                    file_name=?,
                    file_path=?,
                    uploaded_at=?

                WHERE id=?
            """, (
                original_name,
                file_path,
                uploaded_at,
                existing["id"]
            ))


        else:

            conn.execute("""
                INSERT INTO resume
                (
                    user_id,
                    file_name,
                    file_path,
                    uploaded_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                session["user_id"],
                original_name,
                file_path,
                uploaded_at
            ))


        conn.commit()

        conn.close()


        flash(
            "CV uploaded successfully!",
            "success"
        )


        return redirect(
            url_for("resume")
        )


    # -----------------------------------------------------
    # GET RESUME
    # -----------------------------------------------------

    conn = get_db_connection()


    resume_data = conn.execute("""
        SELECT
            id,
            user_id,
            file_name,
            file_path,
            uploaded_at
        FROM resume
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (
        session["user_id"],
    )).fetchone()


    conn.close()


    # -----------------------------------------------------
    # VARIABLES
    # -----------------------------------------------------

    current_name = session.get(
        "name",
        "User"
    )


    resume_name = (
        resume_data["file_name"]
        if resume_data and resume_data["file_name"]
        else "No resume uploaded yet."
    )


    uploaded_date = ""


    uploaded_time = ""


    if resume_data and resume_data["uploaded_at"]:

        uploaded_value = resume_data[
            "uploaded_at"
        ]


        parts = uploaded_value.split(
            " "
        )


        if len(parts) >= 1:

            uploaded_date = parts[0]


        if len(parts) >= 2:

            uploaded_time = parts[1]


    resume_exists = bool(
        resume_data
    )


    # -----------------------------------------------------
    # HTML
    # -----------------------------------------------------

    html = """
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            CV / Resume - SmartHire
        </title>

        {{ base_style | safe }}

    </head>


    <body>

        {{ navbar_html | safe }}


        <div class="container">


            <div class="hero">

                <div>

                    <h1>
                        CV / Resume
                    </h1>

                    <p>
                        Upload and manage your latest resume.
                    </p>

                </div>

            </div>


            {% with messages =
                get_flashed_messages(
                    with_categories=true
                )
            %}

                {% for category, message in messages %}

                    <div
                        class="flash flash-{{ category }}"
                    >

                        {{ message }}

                    </div>

                {% endfor %}

            {% endwith %}


            <div class="card form-card">


                <h2>
                    📄 Upload Resume
                </h2>


                <p style="
                    color:#64748b;
                ">

                    Accepted formats:
                    PDF, DOC, DOCX

                </p>


                <form
                    method="POST"
                    enctype="multipart/form-data"
                >


                    <div class="form-group">

                        <label class="form-label">

                            Select CV

                        </label>


                        <input
                            type="file"
                            name="resume"
                            class="form-input"
                            accept=".pdf,.doc,.docx"
                            required
                        >

                    </div>


                    <button
                        type="submit"
                        class="btn btn-primary"
                    >

                        ⬆️ Upload CV

                    </button>


                </form>


                <br>


                <div class="panel">


                    <h3>
                        📁 Current Resume
                    </h3>


                    <p>

                        <b>
                            Candidate:
                        </b>

                        {{ current_name }}

                    </p>


                    <p>

                        <b>
                            File Name:
                        </b>

                        {{ resume_name }}

                    </p>


                    {% if uploaded_date %}

                        <p>

                            <b>
                                Uploaded Date:
                            </b>

                            {{ uploaded_date }}

                        </p>

                    {% endif %}


                    {% if uploaded_time %}

                        <p>

                            <b>
                                Uploaded Time:
                            </b>

                            {{ uploaded_time }}

                        </p>

                    {% endif %}


                    {% if resume_exists %}

                        <br>


                        <a
                            href="/resume/view"
                            target="_blank"
                            class="btn btn-success"
                        >

                            👁️ Open CV

                        </a>

                    {% endif %}


                </div>


            </div>


        </div>


    </body>

    </html>
    """


    return render_template_string(
        html,
        base_style=BASE_STYLE,
        navbar_html=navbar(),
        current_name=current_name,
        resume_name=resume_name,
        uploaded_date=uploaded_date,
        uploaded_time=uploaded_time,
        resume_exists=resume_exists
    )


# =========================================================
# VIEW / OPEN CV
# =========================================================

@app.route(
    "/resume/view"
)
@login_required
def view_resume():

    conn = get_db_connection()


    resume_data = conn.execute("""
        SELECT
            file_name,
            file_path
        FROM resume
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (
        session["user_id"],
    )).fetchone()


    conn.close()


    if not resume_data:

        flash(
            "No CV uploaded yet.",
            "error"
        )

        return redirect(
            url_for("resume")
        )


    file_path = resume_data[
        "file_path"
    ]


    if not file_path:

        flash(
            "CV file path is missing.",
            "error"
        )

        return redirect(
            url_for("resume")
        )


    if not os.path.exists(file_path):

        flash(
            "CV file not found in uploads folder.",
            "error"
        )

        return redirect(
            url_for("resume")
        )


    return send_file(
        file_path,
        as_attachment=False,
        download_name=resume_data["file_name"]
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route(
    "/admin-dashboard"
)
@admin_required
def admin_dashboard():

    conn = get_db_connection()


    total_users = conn.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role='candidate'
    """).fetchone()[0]


    total_jobs = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
    """).fetchone()[0]


    total_applications = conn.execute("""
        SELECT COUNT(*)
        FROM applications
    """).fetchone()[0]


    selected = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Selected'
    """).fetchone()[0]


    under_review = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Under Review'
    """).fetchone()[0]


    rejected = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Rejected'
    """).fetchone()[0]


    conn.close()


    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            Admin Dashboard
        </title>

        {BASE_STYLE}

    </head>


    <body>

        {navbar()}


        <div class="container">


            <div class="hero">

                <div>

                    <h1>
                        Admin Dashboard
                    </h1>

                    <p>
                        SmartHire recruitment overview.
                    </p>

                </div>

            </div>


            {{% with messages =
                get_flashed_messages(
                    with_categories=true
                )
            %}}

                {{% for category, message in messages %}}

                    <div class="flash flash-{{{{ category }}}}">

                        {{{{ message }}}}

                    </div>

                {{% endfor %}}

            {{% endwith %}}


            <div class="cards">


                <div class="card">

                    <div class="stat-title">
                        Candidates
                    </div>

                    <div class="stat-number">
                        {total_users}
                    </div>

                </div>


                <div class="card">

                    <div class="stat-title">
                        Jobs
                    </div>

                    <div class="stat-number">
                        {total_jobs}
                    </div>

                </div>


                <div class="card">

                    <div class="stat-title">
                        Applications
                    </div>

                    <div class="stat-number">
                        {total_applications}
                    </div>

                </div>


                <div class="card">

                    <div class="stat-title">
                        Selected
                    </div>

                    <div class="stat-number">
                        {selected}
                    </div>

                </div>


            </div>


            <div class="cards">


                <div class="card">

                    <div class="stat-title">
                        Under Review
                    </div>

                    <div class="stat-number">
                        {under_review}
                    </div>

                </div>


                <div class="card">

                    <div class="stat-title">
                        Rejected
                    </div>

                    <div class="stat-number">
                        {rejected}
                    </div>

                </div>


            </div>


            <div class="panel">

                <h2>
                    Admin Controls
                </h2>


                <a
                    href="/jobs"
                    class="btn btn-primary"
                >
                    Manage Jobs
                </a>


                <a
                    href="/applications"
                    class="btn btn-success"
                >
                    Manage Applications
                </a>


                <a
                    href="/resume"
                    class="btn btn-light"
                >
                    Resume
                </a>

            </div>


        </div>


    </body>

    </html>
    """


    return render_template_string(html)


# =========================================================
# DASHBOARD
# =========================================================

@app.route(
    "/dashboard"
)
@login_required
def dashboard():

    if session.get("role") == "admin":

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )


    return redirect(
        url_for("jobs")
    )


# =========================================================
# 404 ERROR
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <div style="
        font-family:Arial;
        text-align:center;
        padding:100px;
    ">

        <h1>
            404
        </h1>

        <p>
            Page not found.
        </p>

        <a href="/jobs">
            Go to Jobs
        </a>

    </div>
    """, 404


# =========================================================
# 500 ERROR
# =========================================================

@app.errorhandler(500)
def server_error(error):

    return """
    <div style="
        font-family:Arial;
        text-align:center;
        padding:100px;
    ">

        <h1>
            500
        </h1>

        <p>
            Something went wrong.
        </p>

        <a href="/jobs">
            Go to Jobs
        </a>

    </div>
    """, 500


# =========================================================
# START APPLICATION
# =========================================================
    init_db()
if __name__ == "__main__":



    print("")
    print("==========================================")
    print("       SmartHire Application")
    print("==========================================")
    print("")
    print("Server:")
    print("http://127.0.0.1:5000")
    print("")
    print("Admin:")
    print("Email: admin@smarthire.com")
    print("Password: admin123")
    print("")
    print("Student:")
    print("Email: student@smarthire.com")
    print("Password: student123")
    print("")
    print("==========================================")
    print("")


    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
