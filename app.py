import os
import click
from flask import Flask, render_template
from config import Config
from extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    import models  # noqa: F401  (registers tables)

    from routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from routes.resources import bp as resources_bp
    app.register_blueprint(resources_bp)

    from routes.bookings import bp as bookings_bp
    app.register_blueprint(bookings_bp)

    from routes.approvals import bp as approvals_bp
    app.register_blueprint(approvals_bp)

    from routes.lifecycle import bp as lifecycle_bp
    app.register_blueprint(lifecycle_bp)    

    from routes.incidents import bp as incidents_bp
    app.register_blueprint(incidents_bp)

    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "same-origin"
        return resp

    @app.route("/")
    def home():
        return render_template("landing.html")

    @app.errorhandler(404)
    def not_found(e):
        return "Not found", 404

    @app.errorhandler(500)
    def server_error(e):
        return "Something went wrong.", 500  # no internals leaked

    @app.cli.command("init-db")
    @click.option("--seed/--no-seed", default=True)
    def init_db(seed):

        from models import User

        # Create tables without deleting existing data
        db.create_all()

        # Seed only when the database has no users
        if seed and User.query.count() == 0:
            from seed import seed_demo
            seed_demo()

        click.echo("Database initialised successfully.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
