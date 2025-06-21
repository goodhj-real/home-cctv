import os
import cv2
from flask import Flask, render_template, redirect, url_for, send_from_directory
from datetime import datetime
import threading
import time

# Render 환경 여부 확인
IS_RENDER = os.environ.get("RENDER") == "true"

# gpiozero는 라즈베리파이에서만 사용
if not IS_RENDER:
    from gpiozero import DistanceSensor

app = Flask(__name__)

# 사진 저장 디렉토리
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_DIR = os.path.join(BASE_DIR, 'static', 'images', 'manual')
MOTION_DIR = os.path.join(BASE_DIR, 'static', 'images', 'motion')
os.makedirs(MANUAL_DIR, exist_ok=True)
os.makedirs(MOTION_DIR, exist_ok=True)

# 초음파 센서 설정 (라즈베리파이 전용)
if not IS_RENDER:
    sensor = DistanceSensor(echo=24, trigger=23)
    SENSOR_THRESHOLD = 0.2

# 사진 촬영 함수
def capture_image(save_dir):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join(save_dir, filename)
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite(filepath, frame)
        return filename
    return None

# 초음파 감지 루프
def motion_detection_loop():
    while True:
        try:
            if sensor.distance < SENSOR_THRESHOLD:
                print("[감지] 움직임 감지됨")
                capture_image(MOTION_DIR)
                time.sleep(5)
            time.sleep(0.3)
        except Exception as e:
            print("[에러] 감지 루프:", e)
            time.sleep(1)

# 라우팅
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture')
def capture():
    filename = capture_image(MANUAL_DIR)
    if filename:
        return redirect(url_for('latest'))
    return "사진 촬영 실패"

@app.route('/latest')
def latest():
    files = sorted(os.listdir(MANUAL_DIR), reverse=True)
    latest_file = files[0] if files else None
    return render_template('latest.html', filename=latest_file)

@app.route('/gallery')
def gallery():
    files = sorted(os.listdir(MANUAL_DIR), reverse=True)
    return render_template('gallery.html', files=files)

@app.route('/motion-log')
def motion_log():
    files = sorted(os.listdir(MOTION_DIR), reverse=True)
    return render_template('motion_log.html', files=files)

@app.route('/image/<folder>/<filename>')
def image(folder, filename):
    directory = MANUAL_DIR if folder == 'manual' else MOTION_DIR
    return send_from_directory(directory, filename)

# 실행
if __name__ == '__main__':
    if not IS_RENDER:
        threading.Thread(target=motion_detection_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
