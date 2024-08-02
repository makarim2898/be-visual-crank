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

home_page = Blueprint('crank_routes', __name__)
CORS(home_page)
#definitions resolusi gambar input 
width_res = 320
height_res = 240
#definisi variabel global untuk flags
inspectionFlag = False

#definisi global untuk object yang di deteksi
oilseal_thread = 0,
rear_thread = False
keyway_detected = False

#definisi index class object didalam model yolo
oilseal_class_index = 0
rear_thread_class_index = 41
keyway_class_index = 67

#definisi variabel global untuk
latest_frame = None
updateData = {'total_judges': 0,
              'sesion_judges': 0,
              'trigger_start': 0,
              'trigger_reset':0,
              'last_judgement': 'NG',
              }

model1 = YOLO("./models/yolov8m.pt")
model2 = YOLO("./models/yolov8m.pt")
model3 = YOLO("./models/yolov8m.pt")



############## function untuk PLC communication #########

############## function untuk stream frame ke client ################
############## Kamera 1 stream oil seal #############
def stream_video1(device, idx_object_class):
    global latest_frame, rear_thread, inspectionFlag, updateData
    time.sleep(2)
    cap = cv2.VideoCapture(device)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    # Set frame width and height for 16:9 aspect ratio and 1080p resolution
    frame_width = width_res
    frame_height = height_res  # Initial frame height for 16:9 aspect ratio and 720p resolution

    # Calculate the frame width based on the aspect ratio
    frame_width = int((frame_height / 9) * 16)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
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
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Tidak dapat membaca frame")
            break
        
        results = model1(frame, conf=0.7, classes=idx_object_class)
        annotated_frame = results[0].plot()
        
        print(f"deteksi dengan kamera index {device}")
        # dibawah ini logika untuk memperkecil ukuran frame agar ringan saat di show up
        #Set frame width and height for 16:9 aspect ratio and 1080p resolution
        frame_width = 640
        frame_height = 480  # Initial frame height for 16:9 aspect ratio and 720p resolution

        # Calculate the frame width based on the aspect ratio
        frame_width = int((frame_height / 9) * 16)
        annotated_frame = cv2.resize(annotated_frame, (int(frame_width * (810 / frame_height)), 810))
        
        #encoding gambar yang akan di kirim  menjadi jpg
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        #read plc var data
        
        
        #jika trigger untuk deteksi on
        if inspectionFlag:
        # logika untuk mendapatkan data object yang di deteksi
        #kemudian perbarui nilai di global variabel rear_thread
            for r in results:
                detected_object = len(r.boxes.cls)
                if detected_object:
                    save_image(annotated_frame, 'OKE', 'Deteksi_oke')
                    print(f'Detected object: {detected_object}')
                    latest_frame = frame
                    inspectionFlag = False
                else:
                    print('No crank object detected')
                    save_image(annotated_frame, 'NG', 'Tidak_terdeteksi')
                    print(f'Detected object: {detected_object}')
                    latest_frame = frame
                    inspectionFlag = False
            
            update_data_dict('last_judgement', rear_thread)
            update_data_dict('sesion_judges', updateData['sesion_judges']+1)
            update_data_dict('total_judges', updateData['total_judges']+1)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()

############## Kamera 2 stream rear thread #############
def stream_video2(device, idx_object_class):
    global latest_frame, rear_thread, inspectionFlag, updateData
    time.sleep(2)
    cap = cv2.VideoCapture(device)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    # Set frame width and height for 16:9 aspect ratio and 1080p resolution
    frame_width = width_res
    frame_height = height_res  # Initial frame height for 16:9 aspect ratio and 720p resolution

    # Calculate the frame width based on the aspect ratio
    frame_width = int((frame_height / 9) * 16)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
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
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Tidak dapat membaca frame")
            break
        
        results = model2(frame, conf=0.7, classes = idx_object_class)
        annotated_frame = results[0].plot()
        
        print(f"deteksi dengan kamera index {device}")
        # dibawah ini logika untuk memperkecil ukuran frame agar ringan saat di show up
        #Set frame width and height for 16:9 aspect ratio and 1080p resolution
        frame_width = 640
        frame_height = 480  # Initial frame height for 16:9 aspect ratio and 720p resolution

        # Calculate the frame width based on the aspect ratio
        frame_width = int((frame_height / 9) * 16)
        annotated_frame = cv2.resize(annotated_frame, (int(frame_width * (810 / frame_height)), 810))
        
        #encoding gambar yang akan di kirim  menjadi jpg
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        #read plc var data
        
        
        #jika trigger untuk deteksi on
        if inspectionFlag:
        # logika untuk mendapatkan data object yang di deteksi
        #kemudian perbarui nilai di global variabel rear_thread
            for r in results:
                detected_object = len(r.boxes.cls)
                if detected_object:
                    save_image(annotated_frame, 'OKE', 'Deteksi_oke')
                    print(f'Detected object: {detected_object}')
                    latest_frame = frame
                    inspectionFlag = False
                else:
                    print('No crank object detected')
                    save_image(annotated_frame, 'NG', 'Tidak_terdeteksi')
                    print(f'Detected object: {detected_object}')
                    latest_frame = frame
                    inspectionFlag = False
            
            update_data_dict('last_judgement', rear_thread)
            update_data_dict('sesion_judges', updateData['sesion_judges']+1)
            update_data_dict('total_judges', updateData['total_judges']+1)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()

############## Kamera 3 stream key way #############
def stream_video3(device, idx_object_class):
    global latest_frame, rear_thread, inspectionFlag, updateData
    time.sleep(2)
    cap = cv2.VideoCapture(device)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    # Set frame width and height for 16:9 aspect ratio and 1080p resolution
    frame_width = width_res
    frame_height = height_res  # Initial frame height for 16:9 aspect ratio and 720p resolution

    # Calculate the frame width based on the aspect ratio
    frame_width = int((frame_height / 9) * 16)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
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
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Tidak dapat membaca frame")
            break
        
        results = model3(frame, conf=0.7, classes = idx_object_class)
        annotated_frame = results[0].plot()
        
        print(f"deteksi dengan kamera index {device}")
        # dibawah ini logika untuk memperkecil ukuran frame agar ringan saat di show up
        #Set frame width and height for 16:9 aspect ratio and 1080p resolution
        frame_width = 640
        frame_height = 480  # Initial frame height for 16:9 aspect ratio and 720p resolution

        # Calculate the frame width based on the aspect ratio
        frame_width = int((frame_height / 9) * 16)
        annotated_frame = cv2.resize(annotated_frame, (int(frame_width * (810 / frame_height)), 810))
        
        #encoding gambar yang akan di kirim  menjadi jpg
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        #read plc var data
        
        
        #jika trigger untuk deteksi on
        if inspectionFlag:
        # logika untuk mendapatkan data object yang di deteksi
        #kemudian perbarui nilai di global variabel rear_thread
            for r in results:
                detected_object = len(r.boxes.cls)
                if detected_object:
                    save_image(annotated_frame, 'OKE', 'Deteksi_oke')
                    print(f'Detected object: {detected_object}')
                    latest_frame = frame
                    inspectionFlag = False
                else:
                    print('No crank object detected')
                    save_image(annotated_frame, 'NG', 'Tidak_terdeteksi')
                    print(f'Detected object: {detected_object}')
                    latest_frame = frame
                    inspectionFlag = False
            
            update_data_dict('last_judgement', rear_thread)
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
    
############## function untuk loading camera index configuration #################
def update_camera_configuration(camera_id):
    df = pd.read_csv('idx_cam_cfg.csv')
    data_camera = df.loc[df['camera_id'] == camera_id]
    camera_idx  = data_camera['camera_index'].values[0]
    return camera_idx
    
####################### END POINT ##########################
##################### end point streaming video #########################
@home_page.route('/crank/show-video-oilseal', methods=['GET'])
def home_show_oilseal():
    global oilseal_class_index
    camera_id = 1
    idx_camera = update_camera_configuration(camera_id)
    print(f'Settings show video with camera index {idx_camera}')
    return Response(stream_video1(idx_camera, oilseal_class_index), mimetype='multipart/x-mixed-replace; boundary=frame')

@home_page.route('/crank/show-video-thread', methods=['GET'])
def home_show_thread():
    global rear_thread_class_index
    camera_id = 2
    idx_camera = update_camera_configuration(camera_id)
    print(f'Settings show video with camera index {idx_camera}')
    return Response(stream_video2(idx_camera, rear_thread_class_index), mimetype='multipart/x-mixed-replace; boundary=frame')

@home_page.route('/crank/show-video-keyway', methods=['GET'])
def home_show_keyway():
    global keyway_class_index
    camera_id = 3
    idx_camera = update_camera_configuration(camera_id)
    print(f'Settings show video with camera index {idx_camera}')
    return Response(stream_video3(idx_camera, keyway_class_index), mimetype='multipart/x-mixed-replace; boundary=frame')


######################## end point last detections #########################
@home_page.route('/crank/last-detections', methods=['GET'])
def home_show_last():
    return Response(last_detection(), mimetype='multipart/x-mixed-replace; boundary=frame')

####################### end point streaming data json ######################
@home_page.route('/crank/get-data', methods=['GET'])
def get_data():
    global rear_thread
    data = updateData
    print(data['total_judges'])
    # data = {'rear_thread': rear_thread}
    return jsonify(data)


####################### end point start inspection ######################
@home_page.route('/crank/start', methods=['GET'])
def startInspection():
    start_inspection()
    return "sucess startingspection"
#################################################################################################################################
