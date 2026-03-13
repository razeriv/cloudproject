import threading
from bot import start_bot  # Импортируйте функцию старта бота
from app import app     # Импортируйте Flask-приложение

def run_flask_server():
    """Функция для запуска Flask приложения"""
    print("Starting Flask server...")
    # Отключаем debug, чтобы избежать конфликта сигналов
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)

def run_bot():
    """Функция для запуска бота"""
    print("Starting Bot...")
    start_bot()

if __name__ == "__main__":
    # Запускаем Flask сервер в отдельном потоке
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.start()

    # Запускаем бот в главном потоке
    run_bot()