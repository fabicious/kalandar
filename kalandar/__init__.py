from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_NAME = "kalandar.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-replace-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    from .models import User, Event
    
    with app.app_context():
        create_database()
    
    return app

def create_database():
    if not path.exists('kalandar/' + DB_NAME):
        db.create_all()
        print('Created Database!')
