from flask import Blueprint, Response, request, jsonify
from flask_cors import CORS
import cv2
import os
import pandas as pd
import datetime
import numpy as np
import time
from ultralytics import YOLO

home_bearing = Blueprint('bearing_routes', __name__)
CORS(home_bearing)

inspectionFlag = False
bearing_detected = False

model = YOLO("./models/yolov8m.pt")
def stream_video(device):
    global latest_frame, bearing_detected, inspectionFlag
    time.sleep(2)
    cap = cv2.VideoCapture(device)
    
    if not cap.isOpened():
        # Generate a placeholder frame with error message
        error_frame = np.zeros((500, 800, 3), np.uint8)
        pesan_string = f'''Camera index {device} out of range
                            Silahkan tekan Refresh Camera atau Halaman Web
                            jika masih berlanjut Lepas pasang USB pada Camera
                            jika masih error lambaikan tangan pada kamera'''
        cv2.putText(error_frame, pesan_string, (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        ret, buffer = cv2.imencode('.jpg', error_frame)
        error_frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
    
    # Set frame width and height for 16:9 aspect ratio and 1080p resolution
    frame_width = 3840
    frame_height = 2160  # Initial frame height for 16:9 aspect ratio and 720p resolution

    # Calculate the frame width based on the aspect ratio
    frame_width = int((frame_height / 9) * 16)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Tidak dapat membaca frame")
            break
        results = model(frame, conf=0.9, classes=0)
        annotated_frame = results[0].plot()
        
        #jika trigger untuk deteksi on
        if inspectionFlag:
        # logika untuk mendapatkan data object yang di deteksi
        #kemudian perbarui nilai di global variabel bearing_detected
            for r in results:
                detected_object = len(r.boxes.cls)
                if detected_object:
                    bearing_detected = True
                    save_image(annotated_frame, 'OKE', 'Deteksi_oke')
                    print(f'Detected object: {detected_object}')
                    inspectionFlag = False
                else:
                    bearing_detected = False
                    print('No bearing object detected')
                    save_image(annotated_frame, 'NG', 'Tidak_terdeteksi')
                    print(f'Detected object: {detected_object}')
                    inspectionFlag = False
            
                    
        # dibawah ini logika untuk memperkecil ukuran frame agar ringan saat di show up
        #Set frame width and height for 16:9 aspect ratio and 1080p resolution
        frame_width = 1280
        frame_height = 720  # Initial frame height for 16:9 aspect ratio and 720p resolution

        # Calculate the frame width based on the aspect ratio
        frame_width = int((frame_height / 9) * 16)
        annotated_frame = cv2.resize(annotated_frame, (int(frame_width * (810 / frame_height)), 810))
        latest_frame = frame
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()
    
def start_inspection():
    global inspectionFlag
    inspectionFlag = True
    return 

def save_image(images_to_save, raw_file_name, image_category):
    corrected_name = raw_file_name.replace(' ', '_')

    # Get current date and time for saving the file name.
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{corrected_name}_{timestamp}.jpg"
    
    # Buat Direktory download
    current_directory = os.path.dirname(os.path.abspath(__file__))
    downloads_directory = os.path.join(current_directory, f'Downloads/{image_category}')
    os.makedirs(downloads_directory, exist_ok=True)
    
    #simpan ke direktori download
    image_path = os.path.join(downloads_directory, f"{file_name}.png")  # Menambahkan timestamp pada nama file
    
    cv2.imwrite(image_path, images_to_save)
    print(f"Gambar disimpan di {image_path}")
    
    
@home_bearing.route('/bearing/show-video', methods=['GET'])
def settings_show_video():
    id_camera = request.args.get('id_camera', default=0, type=int)
    print(f'Settings show video with camera index {id_camera}')
    return Response(stream_video(id_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@home_bearing.route('/bearing/get-data', methods=['GET'])
def get_data():
    global bearing_detected
    data = {'bearing_detected': bearing_detected}
    return jsonify(data)

@home_bearing.route('/bearing/start', methods=['GET'])
def startInspection():
    start_inspection()
    return "sucess startingspection"