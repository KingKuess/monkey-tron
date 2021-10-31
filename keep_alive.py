from flask import Flask
import os
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "Hello. I am alive!"


def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 33507)))


def keep_alive():
    t = Thread(target=run)
    t.start()
