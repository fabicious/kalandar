from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_NAME = "kalandar.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-replace-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .views import views

    app.register_blueprint(views, url_prefix='/')
    
    from .models import Event
    
    with app.app_context():
        create_database()
    
    return app

def create_database():
    if not path.exists('kalandar/' + DB_NAME):
        db.create_all()
        print('Created Database!')