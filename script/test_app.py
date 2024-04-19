import unittest
from flask import Flask
from hashlib import sha256
from sqlalchemy.exc import IntegrityError
from script import app, connect_to_database, Session
from models import User, Auth
import logging

# Настраиваем логгирование для отслеживания ошибок
logging.basicConfig(filename='test_logs.log', level=logging.INFO)

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

if __name__ == '__main__':
    unittest.main()
