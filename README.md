# Examination Management Portal (EMP)

A role-based web application developed for managing university examination lifecycles, slot generation, student bookings, rubric-based evaluation, and result tracking. Built as part of the **Modern Application Development I (MAD-I)** course project at IIT Madras BS Degree.

---

## 🚀 Key Highlights & Constraints
- **Backend:** Python Flask with modular **Flask Blueprints**
- **Database:** SQLite programmatically modeled using **Flask-SQLAlchemy ORM**
- **Authentication:** **Flask-Login** session-based auth with secure password hashing (`pbkdf2:sha256`)
- **Frontend:** Jinja2 server-side templating styled strictly with **Bootstrap 5**
- **Zero Core JS:** All core flows, form submissions, and data validations operate via standard HTTP request/response lifecycles without client-side JavaScript reliance.

---

## 👥 Role-Based Capabilities

### 1. 🛡️ Administrator (Pre-seeded Superuser)
- **Course Management:** Full CRUD operations on academic courses.
- **Examination Management:** Configure exams, types (Viva, Practical, Project Demo, Assessment), duration, and total marks.
- **Rubrics Management:** Define granular evaluation criteria with custom weightages and maximum marks.
- **Examiner Approval Gate:** Review incoming faculty registrations; approve or deactivate examiners before they gain dashboard access.
- **Global Timelines Control:**
  - **Slot Creation Period:** Opens/closes the window for faculty to create exam slots.
  - **Student Slot Booking Period:** Opens/closes the self-booking portal for students.
- **Slot Administration:** View all slots system-wide, edit details, reschedule slots, or reassign examiners in exceptional situations.
- **Booking Oversight & Results Publishing:** Monitor student reservations, cancel conflicting bookings, and publish evaluated marks to students.

### 2. 🧑‍🏫 Examiner (Faculty)
- **Self-Registration:** Register with Employee ID, Department, and credentials (defaults to `pending` until Admin approval).
- **Slot Creation:** Create availability time blocks with specific dates, times, and student capacity during the slot creation window.
- **Slot Management:** Edit and manage hosted slots and view real-time booked counts.
- **Evaluation & Grading:** Score booked candidates against the examination's multi-criterion rubrics, provide feedback remarks, and submit grades.
- **Results Tracking:** Review all submitted and published evaluation outcomes.

### 3. 🎓 Student (Candidate)
- **Self-Registration:** Register with Roll Number, Name, Year, and Contact info.
- **Examination Discovery:** Browse available examinations open for booking with real-time seat availability.
- **Slot Reservation:** Reserve a seat in preferred examiner slots with strict safeguards against duplicate bookings.
- **Booking Management:** View booking history, personal exam timetable ("My Slots"), and cancel bookings (with automatic seat-count restoration).
- **Result Viewing:** Access comprehensive performance breakdowns with per-rubric scores and examiner feedback once published by Admin.

---

## 📂 Project Structure

```text
ExamControl/
├── app.py                     # Flask application factory, DB init & blueprint registration
├── models/
│   └── models.py              # SQLAlchemy database models, relationships, and constraints
├── routes/
│   ├── __init__.py            # Blueprint package exports
│   ├── auth_routes.py         # Login, student/examiner registration, logout
│   ├── admin_routes.py        # Admin dashboard, CRUD, timelines, results publishing
│   ├── examiner_routes.py     # Examiner slots, assignments, evaluations
│   └── student_routes.py      # Student dashboard, booking, cancellation, results
├── templates/
│   ├── base.html              # Core Bootstrap shell with responsive navigation
│   ├── auth/                  # Login, examiner registration, student registration
│   ├── admin/                 # Courses, exams, rubrics, examiners, students, slots, results
│   ├── examiner/              # Dashboard, assigned exams, slots, evaluation, results
│   └── student/               # Dashboard, available exams, slots, bookings, results, profile
├── instance/
│   └── examcontrol.sqlite     # SQLite database file
├── seed_data.py               # Pre-seeding script with realistic academic sample data
├── pyproject.toml             # Project dependency specification
└── README.md                  # Project documentation
```

---

## 🛠️ Setup & Local Installation

### Prerequisites
- Python 3.10+ installed
- `git` installed

### 1. Clone the Repository
```bash
git clone https://github.com/25f3004638/ExamControl.git
cd ExamControl
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install flask flask-sqlalchemy flask-login
```

### 4. Initialize Database & Seed Sample Data
The database tables and initial Admin superuser are automatically created when the app boots. To populate comprehensive demo data (courses, approved/pending examiners, active exams, slots, and evaluations):
```bash
python seed_data.py
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🔑 Default Login Credentials (Demo Accounts)

| Role | Email | Password | Description / Use Case in Demo |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@emp.com` | `admin123` | System Superuser (Full access) |
| **Examiner** | `examiner@emp.com` | `examiner123` | **Dr. Arvind Kumar** (Approved; has active slots and evaluations) |
| **Examiner** | `priya@emp.com` | `examiner123` | **Dr. Priya Sharma** (Approved examiner) |
| **Examiner (Pending)** | `rajesh@emp.com` | `examiner123` | **Prof. Rajesh Verma** (Pending; demo Admin approval workflow) |
| **Student 1** | `student@emp.com` | `student123` | **Rahul Mehta** (`25f3004638`; has published exam results) |
| **Student 2** | `sneha@emp.com` | `student123` | **Sneha Patel** (Has submitted eval ready for Admin to publish) |
| **Student 3** | `amit@emp.com` | `student123` | **Amit Sharma** (Fresh student ready to book open slots) |

---

## 📊 Database Schema Summary

- **`users`:** Core credentials, hashed passwords, roles (`admin`, `examiner`, `student`).
- **`examiners`:** 1-to-1 extension of `users`, employee ID, department, approval status (`pending`, `approved`, `inactive`).
- **`students`:** 1-to-1 extension of `users`, roll number, year, enrolled course.
- **`courses`:** Course code, title, description, department relation.
- **`examinations`:** Linked to course, exam type, duration, max marks, timeline timestamps, lifecycle status (`draft`, `slot_creation`, `booking_open`, `closed`, `completed`).
- **`rubrics`:** Multi-criterion rubrics per exam with individual weightages and max marks.
- **`examination_slots`:** Examiner-hosted time blocks with max capacity and real-time available seats.
- **`bookings`:** Student reservations with unique constraint `(student_id, slot_id)` preventing duplicate reservations.
- **`evaluations` & `evaluation_scores`:** Granular per-rubric grading records, examiner feedback, total score computation, and status gating (`draft`, `submitted`, `published`).

---

## 🤖 Declaration of AI Usage
- **Reported AI Usage Percentage:** **10%**
- **Specific Tasks Assisted by AI:**
  - Generating initial Bootstrap 5 HTML boilerplate structures and CSS layout alignments.
  - Assisting in syntax debugging for SQLAlchemy session flush operations.
  - Reviewing and formatting markdown documentation.
- **Student Ownership (90%):** Core conceptual design, architectural organization, relational database modeling, business validation rules, role-based workflows, and testing.

---

## 📜 License
Developed for academic assessment in the IIT Madras BS Degree program.
