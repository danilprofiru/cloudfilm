from flask import Flask, request, Response
import subprocess
from urllib.parse import quote


app = Flask(__name__)
ffmpeg_process = None  # объявляем переменную ffmpeg_process

@app.route('/create_stream', methods=['POST'])
def create_stream():
    global ffmpeg_process  # делаем переменную глобальной
    if ffmpeg_process is not None:
        return "A stream is already running", 400

    file_name = request.form.get('file_name')
    if not file_name:
        return "The file name is not specified", 400

    encoded_file_name = quote(file_name, safe='')
    encoded_file_name = encoded_file_name.replace('+', '%20')

    ffmpeg_cmd = f"ffmpeg -re -i {file_name} -c:v copy -c:a aac -f flv rtmp://192.168.1.13/myapp/{encoded_file_name}"

    try:
        ffmpeg_process = subprocess.Popen(ffmpeg_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return Response(ffmpeg_process.stdout, mimetype='video/flv')
    except Exception as e:
        return f"An error occurred at startup ffmpeg: {e}", 500

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process = None  # сбрасываем переменную после завершения процесса
        return "Streaming stopped successfully", 200
    else:
        return "No stream is currently running", 400

@app.route('/change_speed', methods=['POST'])
def change_speed():
    global ffmpeg_process

    speed = request.form.get('speed')

    if speed not in ['0.5', '1.5', '2']:
        return "Invalid speed value. Allowed values are '0.5', '1.5', '2'", 400

    if ffmpeg_process:
        ffmpeg_process.stdin.write(f'change_speed {speed}\n'.encode())
        return f"Speed changed to {speed}x successfully", 200
    else:
        return "No stream is currently running", 400

@app.route('/pause_resume_stream', methods=['POST'])
def pause_resume_stream():
    global ffmpeg_process

    if ffmpeg_process:
        ffmpeg_process.stdin.write('pause\n'.encode())
        return "Stream paused/resumed successfully", 200
    else:
        return "No stream is currently running", 400

@app.route('/rewind_stream', methods=['POST'])
def rewind_stream():
    global ffmpeg_process

    direction = request.form.get('direction')

    if direction not in ['0', '1']:
        return "Invalid direction value. Allowed values are '0' (backward) and '1' (forward)", 400

    if ffmpeg_process:
        if direction == '0':
            ffmpeg_process.stdin.write('seek -10\n'.encode())
            return "Stream rewound 10 seconds successfully", 200
        elif direction == '1':
            ffmpeg_process.stdin.write('seek 10\n'.encode())
            return "Stream forwarded 10 seconds successfully", 200
    else:
        return "No stream is currently running", 400


if __name__ == '__main__':
    app.run(debug=True, host='192.168.1.13', port=8080)
