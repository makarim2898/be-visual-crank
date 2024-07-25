from flask import Blueprint, Response, request
from flask_cors import CORS
import cv2
import os
import json

settings = Blueprint('my_routes', __name__)
CORS(settings)


id_camera = 0
zoom_level = 100
zoom_increment = 10
focus_level = 0
focus_increment = 5

def disable_autofocus_with_v4l2(device, focus_value):
    # Menonaktifkan autofokus
    os.system(f"sudo v4l2-ctl -d {device} -c focus_automatic_continuous=0")
    print("Autofokus dinonaktifkan")

    print("dah masuk fungsi")
    # new_focus = int(input("Set focus :"))
    # Mengatur fokus manual ke nilai tertentu, misalnya 1010
    os.system(f"sudo v4l2-ctl -d {device} -c focus_absolute={focus_value}")
    print(f"Fokus diatur ke {focus_value}")

def setting_zoom(device, zoom_level):
    os.system(f"v4l2-ctl -d {device} -c zoom_absolute={zoom_level}")
    print(f"Zoom diatur ke {zoom_level}")
  
def stream_video(device):
    global zoom_level, focus_level
    cap = cv2.VideoCapture(device)
    
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
        
        #Set frame width and height for 16:9 aspect ratio and 1080p resolution
        frame_width = 1280
        frame_height = 720  # Initial frame height for 16:9 aspect ratio and 720p resolution

        # Calculate the frame width based on the aspect ratio
        frame_width = int((frame_height / 9) * 16)
        frame = cv2.resize(frame, (int(frame_width * (810 / frame_height)), 810))
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()

#untuk straming frame di front end
@settings.route('/settings-show-video', methods=['GET'])
def settings_show_video():
    print(f'Settings show video with camera index {id_camera}')
    return Response(stream_video(id_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

#untuk setting focus dari front end
@settings.route('/settings-focus', methods=['GET'])
def settings_focus():
    global focus_level
    focus = request.args.get('focus')   #membaca data input dari request
    focus_level = focus                 #menyalin nilai current input ke variabel global
    disable_autofocus_with_v4l2(id_camera, focus_value=focus)   #disabling auto focus and setting manual focus
    print("Focus is set to " + focus)
    return Response(focus, mimetype='multipart/')

@settings.route('/settings-zoom', methods=['GET'])
def zoom():
    global zoom_level
    zoom = request.args.get('zoom')   #membaca data input dari request
    zoom_level = zoom                 #menyalin nilai current input ke variabel global
    setting_zoom(id_camera, zoom_level=zoom_level)
    print("Zoom is set to " + zoom)
    return Response(zoom, mimetype='multipart/')

#buat input kamera manual
@settings.route('/settings-camera-index', methods=['GET'])
def set_camera():
    global id_camera
    new_camera = request.args.get('cam_id')   #membaca data input dari request
    new_camera_value = int(new_camera)
        
    if new_camera_value >= 0:
        id_camera = new_camera_value
            
    print(f"Camera id is set to {id_camera}")
    return Response(str(id_camera))

@settings.route('/settings/switch-camera-index', methods=['GET'])
def switch_camera():
    global id_camera
    direction = request.args.get('direction')   #membaca data input dari request
    switch_direction = int(direction)
        
    if switch_direction == 1:
        id_camera = id_camera + 1
        
    else:
        id_camera = id_camera - 1
            
    print(f"Camera id is set to {id_camera}")
    return Response(str(id_camera))

#save amera settings
@settings.route('/settings-save', methods=['GET'])
def save_parameter_camera():
    value = 'sucess save'
    return Response(value, mimetype='multipart/')

@settings.route('/tipu', methods=['GET'])
def tipu_index():
    return "tipu-tipu-index"
