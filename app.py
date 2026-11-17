from flask import Flask
from flask_login import LoginManager
from models.models import db, User, Admin

app = Flask(__name__)

app.config['SECRET_KEY'] = 'change-this-to-something-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///examcontrol.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


from routes import auth_bp, admin_bp, examiner_bp, student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(examiner_bp, url_prefix='/examiner')
app.register_blueprint(student_bp, url_prefix='/student')


def create_tables():
    db.create_all()

    admin_user = User.query.filter_by(role='admin').first()
    
    if admin_user is None:
        admin_user = User(email='admin@emp.com', role='admin', is_active=True)
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        db.session.flush()

        admin_profile = Admin(user_id=admin_user.id, name='Admin')
        db.session.add(admin_profile)
        db.session.commit()
        print("Admin user created: admin@emp.com / admin123")

with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=True)
