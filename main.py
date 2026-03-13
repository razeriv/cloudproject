import threading
from bot import start_bot
from app import app

def run_flask_server():
    print("Starting Flask server...")
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)

def run_bot():
    print("Starting Bot...")
    start_bot()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.start()

    run_bot()
