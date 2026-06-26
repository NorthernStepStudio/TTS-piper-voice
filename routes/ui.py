from flask import Blueprint, render_template, request

from config import VOICES

ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/")
def index():
    base_url = request.host_url.rstrip("/")
    return render_template("index.html", voices=VOICES, base_url=base_url)
