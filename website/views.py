from flask import Blueprint, render_template, redirect, url_for, Response
from flask_login import login_required, current_user
from functools import wraps
import cv2

views = Blueprint("views", __name__)


# ---- Role helpers ----------------------------------------------------------
def role_required(role):
    """Allow only users with a specific role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if getattr(current_user, "role", "customer") != role:
                # Non-developers get sent to their dashboard
                return redirect(url_for("views.customer_dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---- Landing decides dashboard by role -------------------------------------
@views.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.role == "developer":
            return redirect(url_for("views.developer_dashboard"))
        return redirect(url_for("views.customer_dashboard"))
    return redirect(url_for("auth.login"))


# ---- Dashboards -------------------------------------------------------------
@views.route("/customer")
@login_required
def customer_dashboard():
    return render_template("customer_dashboard.html", user=current_user)


@views.route("/developer")
@login_required
@role_required("developer")
def developer_dashboard():
    return render_template("developer_dashboard.html", user=current_user)


# ---- Webcam (OpenCV MJPEG stream) ------------------------------------------
def gen_frames(camera_index: int = 1):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        # If camera can't open, stop the generator (browser will show broken image)
        return
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    finally:
        cap.release()


@views.route("/webcam")
@login_required
def webcam_page():
    # Page with an <img> that points to the MJPEG stream
    return render_template("webcam.html", user=current_user)


@views.route("/video_feed")
@login_required
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")
