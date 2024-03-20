import unittest
from flask import Flask
from script import app

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

if __name__ == '__main__':
    unittest.main()
