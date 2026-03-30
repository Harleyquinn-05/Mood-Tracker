import os
import base64
from datetime import datetime
from flask import Flask, request, jsonify

from main import DB_PATH

app = Flask(__name__)

print("DB PATH:", os.path.abspath(DB_PATH))


@app.route('/capture_suspicious', methods=['POST'])
def capture_suspicious():

    data = request.json['image']
    image_data = data.split(",")[1]

    filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".png"
    filepath = os.path.join("static/suspicious", filename)

    with open(filepath, "wb") as f:
        f.write(base64.b64decode(image_data))

    return jsonify({"status": "saved"})