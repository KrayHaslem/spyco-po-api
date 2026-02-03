import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from db import db

load_dotenv()


def setup_logging(app):
    """Configure logging to output to both console and file."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler - always show logs in terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # File handler - rotating log file (max 10MB, keep 5 backups)
    # Only log errors to file to keep logs concise
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    
    # Get the root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to avoid duplicates
    root_logger.handlers = []
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Also configure Flask's logger
    app.logger.handlers = []
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)

# Fixed UUID for the Repairs department to ensure consistency
REPAIRS_DEPARTMENT_ID = "00000000-0000-0000-0000-000000000001"


def seed_repairs_department():
    """Create the Repairs department if it doesn't exist."""
    from models import Department
    
    repairs_dept = Department.query.filter_by(id=REPAIRS_DEPARTMENT_ID).first()
    if not repairs_dept:
        repairs_dept = Department(
            id=REPAIRS_DEPARTMENT_ID,
            name="Repairs",
            description="Department for repair request approvals",
            is_active=True,
        )
        db.session.add(repairs_dept)
        db.session.commit()
        print("Repairs department created: ", REPAIRS_DEPARTMENT_ID)


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    app.config["JWT_ALGORITHM"] = os.getenv("JWT_ALGORITHM", "HS256")

    # Set up logging before anything else
    setup_logging(app)

    CORS(
        app,
        supports_credentials=True,
        origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    )

    db.init_app(app)

    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.order_routes import order_bp
    from routes.po_group_routes import po_group_bp
    from routes.lookup_routes import lookup_bp
    from routes.repair_routes import repair_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(order_bp, url_prefix="/api/order")
    app.register_blueprint(po_group_bp, url_prefix="/api/po-group")
    app.register_blueprint(lookup_bp, url_prefix="/api/lookup")
    app.register_blueprint(repair_bp, url_prefix="/api/repair")

    with app.app_context():
        db.create_all()
        seed_repairs_department()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
