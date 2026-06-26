from flask import Flask

from extensions import cors, limiter
from routes.ui import ui_bp
from routes.api import api_bp


def create_app() -> Flask:
    app = Flask(__name__)

    # Extensions
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    limiter.init_app(app)

    # Blueprints
    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
