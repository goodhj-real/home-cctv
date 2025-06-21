from flask import Flask, render_template, redirect, url_for, send_from_directory
import cv2
import os
from datetime import datetime
from gpiozero import DistanceSensor
import threading
import time

app = Flask(__name__)

# 디렉토리 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_DIR = os.path.join(BASE_DIR, 'static', 'images', 'manual')
MOTION_DIR = os.path.join(BASE_DIR, 'static', 'images', 'motion')

# 디렉토리 생성
os.makedirs(MANUAL_DIR, exist_ok=True)
os.makedirs(MOTION_DIR, exist_ok=True)

# 초음파 센서 설정
sensor = DistanceSensor(echo=24, trigger=23)
SENSOR_THRESHOLD = 0.2  # 미터 단위 (0.2m = 20cm)


# 사진 찍기 함수
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


# 초음파 감지 스레드
def motion_detection_loop():
    while True:
        try:
            if sensor.distance < SENSOR_THRESHOLD:
                print("[감지] 움직임 감지됨 → 사진 촬영")
                capture_image(MOTION_DIR)
                time.sleep(5)  # 중복 방지 대기
            time.sleep(0.3)
        except Exception as e:
            print("[에러] 감지 루프:", e)
            time.sleep(1)


# 웹 라우팅 ---------------------------

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


if __name__ == '__main__':
    # 감지 스레드 시작
    threading.Thread(target=motion_detection_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
