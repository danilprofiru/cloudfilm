from flask import Flask, request, Response, jsonify
from argon2 import PasswordHasher
import subprocess
import uuid
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Auth

app = Flask(__name__)

# Создайом экземпляр PasswordHasher
ph = PasswordHasher()

# Подключение к базе данных
def connect_to_database():
    dbname = 'cloudfilm_database'
    user = 'sadmin'
    password = 'adminrbt2300'
    host = '192.168.1.14'
    port = '5432'
    conn_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    try:
        engine = create_engine(conn_string)
        print("Successfully connected to PostgreSQL.")
        return engine
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# Создание фабрики сессий
engine = connect_to_database()
Session = sessionmaker(bind=engine)

# объявляем переменную ffmpeg_process
ffmpeg_process = None

# Маршрут для проверки подключения к приложению через браузер
@app.route('/')
def home():
    return "Welcome to the Flask Application! The connection is successful."

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

    ffmpeg_cmd = f"ffmpeg -re -i {file_name} -c:v copy -c:a aac -f flv rtmp://localhost/myapp/{encoded_file_name}"

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
        try:
            ffmpeg_process.stdin.write('pause\n'.encode())
            return "Stream paused/resumed successfully", 200
        except Exception as e:
            print(f"An error occurred: {e}")  # Выводим сообщение об ошибке для отладки
            return "An error occurred", 400  # Возвращаем код 400 в случае ошибки
    else:
        return "No stream is currently running", 400

@app.route('/rewind_stream', methods=['POST'])
def rewind_stream():
    global ffmpeg_process

    if ffmpeg_process and hasattr(ffmpeg_process, 'stdin'):
        direction = request.form.get('direction')

        if direction not in ['0', '1']:
            return "Invalid direction value. Allowed values are '0' (backward) and '1' (forward)", 400

        try:
            if direction == '0':
                ffmpeg_process.stdin.write('seek -10\n'.encode())
                return "Stream rewound 10 seconds successfully", 200
            elif direction == '1':
                ffmpeg_process.stdin.write('seek 10\n'.encode())
                return "Stream forwarded 10 seconds successfully", 200
        except Exception as e:
            print(f"An error occurred: {e}")  # Выводим сообщение об ошибке для отладки
            return "An error occurred", 500  # Возвращаем код 500 в случае ошибки
    else:
        return "No stream is currently running", 404  # Возвращаем код 404, если поток не запущен

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required'}), 400
    
    with Session() as session:
        # Проверка существования пользователя с таким email
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            return jsonify({'error': 'Email already in use'}), 400
        
        # Хэширование пароля с использованием argon2
        hashed_password = ph.hash(password)
        
        # Создание нового пользователя
        new_user = User(name=name, email=email)
        session.add(new_user)
        session.commit()

        # Создание записи в таблице auth с хэшированным паролем
        new_auth = Auth(userid=new_user.userid, email=email, password=hashed_password)
        session.add(new_auth)
        session.commit()

        return jsonify({'message': 'User registered successfully', 'user_id': new_user.userid}), 201

# Маршрут для аутентификации пользователя
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    with Session() as session:
        auth = session.query(Auth).filter(Auth.email == email).first()
        
        if auth:
            try:
                # Проверка пароля с использованием argon2
                ph.verify(auth.password, password)
                return jsonify({'message': 'Login successful'}), 200
            except argon2.exceptions.VerifyMismatchError:
                return jsonify({'error': 'Invalid password'}), 401
            except ValueError as e:
                # Логгирование ошибки
                print(f"Error during argon2 password check: {e}")
                return jsonify({'error': 'An error occurred during password validation'}), 500
        else:
            return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8082)
