from flask import Flask
from threading import Thread
import os
from waitress import serve  # Production-ready WSGI server

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    # Gumamit ng port mula sa environment o default sa 8080
    port = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
