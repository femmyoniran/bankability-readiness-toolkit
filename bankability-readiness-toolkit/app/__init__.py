from flask import Flask
from config import config_map


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    from app.routes.main_routes import main_bp
    from app.routes.project_routes import project_bp
    from app.routes.analysis_routes import analysis_bp
    from app.routes.report_routes import report_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(project_bp, url_prefix="/project")
    app.register_blueprint(analysis_bp, url_prefix="/analysis")
    app.register_blueprint(report_bp, url_prefix="/report")

    return app
