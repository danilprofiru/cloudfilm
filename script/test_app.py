import unittest
import uuid
from uuid import uuid4
import argon2
from flask import Flask, json
from sqlalchemy.exc import IntegrityError
from script import app, connect_to_database, Session
from models import User, Auth
from argon2 import PasswordHasher

# Создаем экземпляр PasswordHasher
ph = PasswordHasher()

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_create_stream(self):
        response = self.app.post('/create_stream', data={'file_name': 'test.mp4'})
        self.assertEqual(response.status_code, 200)

    def test_stop_stream(self):
        response = self.app.post('/stop_stream')
        self.assertEqual(response.status_code, 200)

    def test_change_speed_valid(self):
        response = self.app.post('/change_speed', data={'speed': '1.5'})
        self.assertEqual(response.status_code, 400)

    def test_change_speed_invalid(self):
        response = self.app.post('/change_speed', data={'speed': '3'})
        self.assertEqual(response.status_code, 400)

    def test_pause_resume_stream(self):
        response = self.app.post('/pause_resume_stream')
        self.assertEqual(response.status_code, 400)

    def test_rewind_stream(self):
        response = self.app.post('/rewind_stream', data={'direction': '0'})
        self.assertEqual(response.status_code, 500)

class TestConnectToDatabase(unittest.TestCase):
    def test_connect_to_database(self):
        engine = connect_to_database()
        with engine.connect() as conn:
            self.assertIsNotNone(conn)

class TestRegisterRoute(unittest.TestCase):

    def setUp(self):
        # Создаем тестовый клиент Flask для использования в тестах
        self.app = app.test_client()
        # Создаем контекст приложения
        self.context = app.app_context()
        self.context.push()

        # Создаем тестовую сессию и базу данных
        self.session = Session()

    def tearDown(self):
        # Удаляем данные, созданные в процессе тестирования
        self.session.query(Auth).delete()
        self.session.query(User).delete()
        self.session.commit()

        # Закрываем сессию и контекст приложения
        self.session.close()
        self.context.pop()

    def test_successful_registration(self):
        data = {
            'name': 'Test User',
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }
        response = self.app.post('/register', json=data)
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('user_id', response_data)

        # Проверяем что пользователь был добавлен в базу данных
        user = self.session.query(User).filter_by(email='testuser@example.com').first()
        self.assertIsNotNone(user)
        # Проверяем что user_id соответствует ожидаемому формату UUID
        self.assertIsInstance(user.userid, uuid.UUID)

    def test_missing_data(self):
        data = {
            'name': '',  # Пустое имя
            'email': '',  # Пустой email
            'password': ''  # Пустой пароль
        }
        response = self.app.post('/register', json=data)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Name, email, and password are required')

    def test_duplicate_email(self):
        # Регистрация пользователя с повторяющимся email
        data = {
            'name': 'Test User',
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }
        self.app.post('/register', json=data)

        # Попытка регистрации с тем же email
        response = self.app.post('/register', json=data)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Email already in use')

class TestLoginRoute(unittest.TestCase):
    def setUp(self):
        # Создаем тестовый клиент Flask для использования в тестах
        self.app = app.test_client()
        # Создаем контекст приложения
        self.context = app.app_context()
        self.context.push()

        # Создаем тестовую сессию и базу данных
        self.session = Session()

        user_id = str(uuid4())

        # Удаляем существующего пользователя с тестовым email
        self.session.query(User).filter(User.email == 'testuser@example.com').delete()
        self.session.commit()

        # Создаем запись в таблице User
        test_user = User(userid=user_id, name='Test User', email='testuser@example.com')
        self.session.add(test_user)
        self.session.commit()

        # Теперь у нас есть userid, который существует в таблице User
        # Используем этот userid для создания записи в таблице auth

        hashed_password = ph.hash('testpassword')
        test_auth = Auth(authid=test_user.userid, email='testuser@example.com', password=hashed_password)
        self.session.add(test_auth)
        self.session.commit()

    def tearDown(self):
        # Удаляем данные, созданные в процессе тестирования
        self.session.query(Auth).filter(Auth.email == 'testuser@example.com').delete()
        self.session.query(User).filter(User.email == 'testuser@example.com').delete()
        self.session.commit()

        # Закрываем сессию и контекст приложения
        self.session.close()
        self.context.pop()

    def test_successful_login(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }
        response = self.app.post('/login', json=data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Login successful')

    def test_invalid_password(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.app.post('/login', json=data)
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Invalid password')

    def test_user_not_found(self):
        data = {
            'email': 'nonexistent@example.com',
            'password': 'any_password'
        }
        response = self.app.post('/login', json=data)
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'User not found')

    def test_missing_email_or_password(self):
        data = {
            'email': '',
            'password': ''
        }
        response = self.app.post('/login', json=data)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Email and password are required')

if __name__ == '__main__':
    unittest.main()
