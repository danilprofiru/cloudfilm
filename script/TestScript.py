import pytest
import requests
from threading import Thread
from script import app

@pytest.fixture(scope="module")
def test_client():
    # Запускаем сервер Flask в отдельном потоке
    server_thread = Thread(target=app.run, kwargs={'debug': True, 'host': '192.168.1.13', 'port': 8080})
    server_thread.start()
    
    # Позволяем некоторое время для запуска сервера
    import time
    time.sleep(1)

    # Создаем клиент для тестирования
    client = app.test_client()

    yield client  # Предоставляем клиента для тестов

    # Завершаем работу сервера Flask
    requests.post('http://192.168.1.13:8080/stop_stream')  # Останавливаем поток
    server_thread.join()

def test_create_stream(test_client):
    file_name = 'example.flv'
    response = test_client.post('/create_stream', data={'file_name': file_name})
    assert response.status_code == 200
    # Проверяем, что процесс FFmpeg был запущен успешно
    assert response.data

def test_stop_stream(test_client):
    response = test_client.post('/stop_stream')
    assert response.status_code == 200
    # Проверяем, что поток был остановлен успешно
    assert response.data == b"Streaming stopped successfully"
