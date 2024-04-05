from flask import Flask, request, Response
from urllib.parse import quote
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
import subprocess
import psycopg2
import hashlib
import random


Base = declarative_base()

# Определение таблиц User и Auth
class User(Base):
    __tablename__ = 'User'
    UserID = Column(Integer, primary_key=True)
    Name = Column(String(100))
    email = Column(String, unique=True, nullable=False)
    auth = relationship("Auth", back_populates="user")

class Auth(Base):
    __tablename__ = 'Auth'
    AuthId = Column(Integer, ForeignKey('User.UserID'), primary_key=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    user = relationship("User", back_populates="auth")

# Подключение к БД
def connect_to_database():
    dbname = 'cloudfilm_database'
    user = 'sadmin'
    password = 'adminrbt2300'
    host = '192.168.1.14'
    port = '5432'
    conn_string = f"dbname='{dbname}' user='{user}' password='{password}' host='{host}' port='{port}'"
    try:
        conn = psycopg2.connect(conn_string)
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return None

Session = sessionmaker(bind=connect_to_database())

# Функция генерации уникального UserID
def generate_unique_userid(session):
    while True:
        random_userid = random.randint(100000, 999999)
        existing_user = session.query(User).filter_by(UserID=random_userid).first()
        if not existing_user:
            return random_userid

# Функция регистрации нового пользователя
def register_user(name, email, password):
    session = Session()
    try:
        userid = generate_unique_userid(session)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        new_user = User(UserID=userid, Name=name, email=email)
        session.add(new_user)
        new_auth = Auth(AuthId=userid, email=email, password=hashed_password)
        session.add(new_auth)
        session.commit()
        return {'message': 'User registered successfully', 'UserID': userid}, 201
    except IntegrityError:
        session.rollback()
        return {'error': 'Integrity error occurred'}, 500
    finally:
        session.close()

# Функция авторизации нового пользователя
def authenticate_user(email, password):
    session = Session()
    try:
        user_auth = session.query(Auth).filter_by(email=email).first()
        if user_auth:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if user_auth.password == hashed_password:
                user = session.query(User).filter_by(UserID=user_auth.AuthId).first()
                return {'UserID': user.UserID, 'Name': user.Name, 'email': user.email}, 200
            else:
                return {'error': 'Invalid email or password'}, 401
        else:
            return {'error': 'Invalid email or password'}, 401
    finally:
        session.close()

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
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required'}), 400

    result, status_code = register_user(name, email, password)
    return jsonify(result), status_code


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    result, status_code = authenticate_user(email, password)
    return jsonify(result), status_code

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8082)
