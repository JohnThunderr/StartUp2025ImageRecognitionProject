from flask import Blueprint, render_template, redirect, url_for, Response
from flask_login import login_required, current_user
from ultralytics import YOLO
from functools import wraps
import cv2

views = Blueprint("views", __name__)

model = YOLO("tree_detection.pt")  # Load your custom-trained model
CONF_THRESH = 0.6  


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
def gen_frames(camera_index: int = 0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            
            results = model(frame, conf=CONF_THRESH)
            annotated = results[0].plot()

            boxes = results[0].boxes
            confs = boxes.conf.tolist()

            # Count trees (class 0) above confidence threshold
            tree_count = sum(
                1
                for cls_id, conf in zip(boxes.cls.tolist(), confs)
                if int(cls_id) == 0 and conf >= CONF_THRESH
            )

            # Annotate frame with tree count
            cv2.putText(
                annotated,
                f"Trees: {tree_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )

            _, buffer = cv2.imencode(".jpg", annotated)
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
