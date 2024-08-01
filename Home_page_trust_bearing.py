from flask import Blueprint, Response, request, jsonify
from flask_cors import CORS
import cv2
import os
import pandas as pd
import datetime
import numpy as np
import time
from ultralytics import YOLO
import serial

home_bearing = Blueprint('bearing_routes', __name__)
CORS(home_bearing)

#definisi variabel global untuk flags
inspectionFlag = False
bearing_detected = False

#definisi variabel global untuk
latest_frame = None
updateData = {'total_judges': 0,
              'sesion_judges': 0,
              'trigger_start': 0,
              'trigger_reset':0,
              'last_judgement': 'NG',
              }

model = YOLO("./models/yolov8m.pt")

############## function untuk arduino communication #########
def init_serial_connection():
    global arduino
    while True:
        print("init_serial_connection called")
        try:
            arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)  # Initialize the Arduino port with shorter timeout
            if arduino.isOpen():  # Check if the serial port is open
                arduino.close()  # Close the port if it is open
            arduino.open()  # Reopen the serial port
            print("Connection established.")
            break  # Exit the loop if successful
        except serial.SerialException as e:
            print(f"Serial connection error during initialization: {e}")
            print("Waiting for connection...")
            time.sleep(5)  # Wait for 5 seconds before trying again

def baca_data_arduino():
    global arduino, inspectionFlag
    while True:
        try:
            input_data = arduino.readline().strip().decode('utf-8')
            if input_data == "start_scan":
                print(f"FROM ARDUINO: {input_data}")
                inspectionFlag = True
                break
            elif input_data == "no trigger":
                print(f"FROM ARDUINO: {input_data}")
                inspectionFlag = False
                break
        except serial.SerialException:
            print("Serial connection error. Waiting for reconnection...")
            arduino.close()
            init_serial_connection()  # Reinitialize the serial connection
        except UnicodeDecodeError:
            print("Error decoding input data.")
    
    

############## function untuk stream frame ke client ################
def stream_video(device):
    global latest_frame, bearing_detected, inspectionFlag, updateData
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
                    
        # dibawah ini logika untuk memperkecil ukuran frame agar ringan saat di show up
        #Set frame width and height for 16:9 aspect ratio and 1080p resolution
        frame_width = 1280
        frame_height = 720  # Initial frame height for 16:9 aspect ratio and 720p resolution

        # Calculate the frame width based on the aspect ratio
        frame_width = int((frame_height / 9) * 16)
        annotated_frame = cv2.resize(annotated_frame, (int(frame_width * (810 / frame_height)), 810))
        
        #encoding gambar yang akan di kirim  menjadi jpg
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        #read arduino data serial
        baca_data_arduino()
        
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
                    latest_frame = frame
                    inspectionFlag = False
                else:
                    bearing_detected = False
                    print('No bearing object detected')
                    save_image(annotated_frame, 'NG', 'Tidak_terdeteksi')
                    print(f'Detected object: {detected_object}')
                    latest_frame = frame
                    inspectionFlag = False
            
            update_data_dict('last_judgement', bearing_detected)
            update_data_dict('sesion_judges', updateData['sesion_judges']+1)
            update_data_dict('total_judges', updateData['total_judges']+1)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()


############## Function untuk start inspection #################
def start_inspection():
    global inspectionFlag
    inspectionFlag = True
    return 

############## Function untuk save images #################
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

############## Function untuk menampilkan last detection #################
def last_detection():
    global latest_frame
    while True:
        if latest_frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
        else:
            # Generate a placeholder frame with a message if no frame is available
            placeholder_frame = np.zeros((500, 800, 3), np.uint8)
            message = "No frame available"
            cv2.putText(placeholder_frame, message, (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', placeholder_frame)
            placeholder_frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + placeholder_frame + b'\r\n')
        time.sleep(0.1)  # Add a small delay to avoid high CPU usage

############## Function untuk update data #################
def update_data_dict(key, value):
    global updateData
    updateData[key] = value
    

####################### END POINT ##########################
@home_bearing.route('/bearing/show-video', methods=['GET'])
def home_show_video():
    id_camera = request.args.get('id_camera', default=0, type=int)
    init_serial_connection()
    print(f'Settings show video with camera index {id_camera}')
    return Response(stream_video(id_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@home_bearing.route('/bearing/last_detections', methods=['GET'])
def home_show_last():
    return Response(last_detection(), mimetype='multipart/x-mixed-replace; boundary=frame')

@home_bearing.route('/bearing/get-data', methods=['GET'])
def get_data():
    global bearing_detected
    data = updateData
    print(data['total_judges'])
    # data = {'bearing_detected': bearing_detected}
    return jsonify(data)

@home_bearing.route('/bearing/start', methods=['GET'])
def startInspection():
    start_inspection()
    return "sucess startingspection"