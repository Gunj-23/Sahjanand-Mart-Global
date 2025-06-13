import os
import sys
import subprocess
import time
import webbrowser
from threading import Thread

PROJECT_ROOT = r"D:\sahjanand_mart-Copy"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def run_flask_app():
    os.chdir(os.path.join(PROJECT_ROOT, 'backend'))
    subprocess.Popen(['python', 'app.py'])

def open_browser():
    time.sleep(3)  # Increased delay to ensure server is ready
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    try:
        os.chdir(PROJECT_ROOT)
        print(f"Starting Sahjanand Mart from: {PROJECT_ROOT}")
        
        flask_thread = Thread(target=run_flask_app)
        flask_thread.daemon = True
        flask_thread.start()
        
        open_browser()
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to exit...")