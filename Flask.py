import os
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect
from PIL import Image
import numpy as np
import requests
from werkzeug.utils import secure_filename
from model import get_caption_model, generate_caption

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

caption_model = get_caption_model()

def preprocess_image(image):
    image = image.convert('RGB')
    image = image.resize((299, 299))
    image = np.array(image) / 255.0
    return image

def generate_caption_for_uploaded_image(uploaded_image):
    uploaded_image = preprocess_image(uploaded_image)
    caption = generate_caption(uploaded_image, caption_model)
    return caption

def generate_caption_for_url_image(image_url):
    response = requests.get(image_url, stream=True)
    image = Image.open(response.raw)
    image = preprocess_image(image)
    caption = generate_caption(image, caption_model)
    return caption

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        try:
            caption = generate_caption_for_uploaded_image(Image.open(image_path))
            return jsonify({"caption": caption, "image_path": "/" + image_path})
        except Exception as e:
            return jsonify({"error": "Error processing the uploaded image."}), 500
    else:
        return jsonify({"error": "Invalid file type."}), 400


@app.route("/upload-url", methods=["POST"])
def upload_url():
    if request.method == "POST":
        if 'url' in request.json:
            url = request.json['url']
            try:
                caption = generate_caption_for_url_image(url)
                return jsonify({"caption": caption, "image_url": url})
            except Exception as e:
                return jsonify({"error": "Error processing image from URL."}), 500
        else:
            return jsonify({"error": "No URL provided."}), 400

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run(debug=True)