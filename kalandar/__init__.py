from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
import os

db = SQLAlchemy()
DB_NAME = "kalandar.db"
BASE_DIR = path.abspath(path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    db_path = path.join(BASE_DIR, DB_NAME)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .views import views

    app.register_blueprint(views, url_prefix='/')

    from .models import Event

    with app.app_context():
        create_database()

    return app

def create_database():
    db_path = path.join(BASE_DIR, DB_NAME)
    if not path.exists(db_path):
        from .models import Event
        db.create_all()
    else:
        _migrate_database()

def _migrate_database():
    """Apply incremental schema changes to existing databases."""
    from sqlalchemy import text
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE event ADD COLUMN all_day BOOLEAN DEFAULT 1"))
            conn.commit()
        except Exception:
            pass  # Column already exists
        try:
            conn.execute(text("ALTER TABLE event ADD COLUMN category VARCHAR(100)"))
            conn.commit()
        except Exception:
            pass  # Column already exists
