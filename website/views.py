from flask import Blueprint, render_template, redirect, url_for, Response, jsonify, request
from flask_login import login_required, current_user
from ultralytics import YOLO
from functools import wraps
import cv2
import threading
import time

views = Blueprint("views", __name__)

# ---- Load YOLO model ----
model = YOLO("tree_detection.pt")
CONF_THRESH = 0.6

# ---- Role helpers ----------------------------------------------------------
def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if getattr(current_user, "role", "customer") != role:
                return redirect(url_for("views.customer_dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ---- Landing page ----------------------------------------------------------
@views.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.role == "developer":
            return redirect(url_for("views.developer_dashboard"))
        return redirect(url_for("views.customer_dashboard"))
    return redirect(url_for("auth.login"))

# ---- Dashboards ------------------------------------------------------------
@views.route("/customer")
@login_required
def customer_dashboard():
    return render_template("customer_dashboard.html", user=current_user)

@views.route("/developer")
@login_required
@role_required("developer")
def developer_dashboard():
    return render_template("developer_dashboard.html", user=current_user)

# ---- Webcam + Detection Variables -----------------------------------------
camera = None
frame_lock = threading.Lock()
latest_frame = None
latest_detections = []
capture_thread = None
detection_thread = None
tree_decisions = {}  # In-memory store for demo

# ---- Capture thread: grab raw frames for immediate display -----------------
def capture_frames():
    global latest_frame, camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("ERROR: Cannot open webcam")
            return

    while True:
        success, frame = camera.read()
        if not success:
            time.sleep(0.05)
            continue
        with frame_lock:
            latest_frame = frame.copy()  # raw frame for instant video

# ---- Detection thread: run YOLO asynchronously ----------------------------
def detect_trees():
    global latest_frame, latest_detections
    while True:
        with frame_lock:
            if latest_frame is None:
                time.sleep(0.05)
                continue
            frame_copy = latest_frame.copy()
        results = model(frame_copy, conf=CONF_THRESH)
        boxes = results[0].boxes
        confs = boxes.conf.tolist()

        trees = []
        for idx, (cls_id, conf, box) in enumerate(zip(boxes.cls.tolist(), confs, boxes.xyxy.tolist())):
            if int(cls_id) == 0 and conf >= CONF_THRESH:
                x1, y1, x2, y2 = [int(coord) for coord in box]
                w = x2 - x1
                h = y2 - y1
                tree_id = f"tree_{idx+1}"
                trees.append({"id": tree_id, "x": x1, "y": y1, "w": w, "h": h, "conf": round(conf,2)})
        with frame_lock:
            latest_detections = trees
        time.sleep(0.05)  # small delay to prevent overload

# ---- Lazy Webcam Start -----------------------------------------------------
@views.route("/webcam")
@login_required
def webcam_page():
    global capture_thread, detection_thread
    if capture_thread is None:
        capture_thread = threading.Thread(target=capture_frames, daemon=True)
        capture_thread.start()
    if detection_thread is None:
        detection_thread = threading.Thread(target=detect_trees, daemon=True)
        detection_thread.start()
    return render_template("webcam.html", user=current_user)

# ---- MJPEG Stream ---------------------------------------------------------
def gen_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            _, buffer = cv2.imencode(".jpg", latest_frame)
            frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

@views.route("/video_feed")
@login_required
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ---- Detections Endpoint --------------------------------------------------
@views.route("/detections")
@login_required
def detections():
    with frame_lock:
        return jsonify({"trees": latest_detections})

# ---- Decision Endpoint ----------------------------------------------------
@views.route("/decision", methods=["POST"])
@login_required
def decision():
    data = request.json
    tree_id = data.get("tree_id")
    choice = data.get("decision")
    if tree_id and choice:
        tree_decisions[tree_id] = choice
        print(f"User {current_user.id} marked {tree_id} as {choice}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Invalid data"}), 400

# ---- Optional: Stop Webcam ------------------------------------------------
@views.route("/webcam/stop")
@login_required
def stop_webcam():
    global camera, capture_thread, detection_thread
    if camera:
        camera.release()
        camera = None
    capture_thread = None
    detection_thread = None
    print("Webcam stopped and threads released.")
    return "Camera released"

