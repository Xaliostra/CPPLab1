import os
import uuid
import requests
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://lively-coast-073979f0f.6.azurestaticapps.net"])

# Конфигурация Azure
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
VISION_API_ENDPOINT = os.getenv("VISION_API_ENDPOINT")
VISION_API_KEY = os.getenv("VISION_API_KEY")

# Инициализация Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def upload_to_azure(file_path):
    """Загружает файл в Azure Blob Storage и возвращает публичный URL"""
    try:
        blob_name = str(uuid.uuid4()) + ".jpg"
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=blob_name)
        
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        return blob_client.url  # Публичный URL загруженного файла
    except Exception as e:
        return None

def analyze_image(image_url):
    """Отправляет изображение в API Computer Vision"""
    if not image_url.startswith("http"):
        return {"error": "Invalid image URL"}
    
    headers = {"Ocp-Apim-Subscription-Key": VISION_API_KEY}
    params = {"visualFeatures": "Tags"}
    data = {"url": image_url}
    
    try:
        response = requests.post(f"{VISION_API_ENDPOINT}/vision/v3.2/analyze", headers=headers, json=data, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    
    image_url = upload_to_azure(file_path)
    if not image_url:
        return jsonify({"error": "Failed to upload image to Azure"}), 500
    
    analysis_result = analyze_image(image_url)
    os.remove(file_path)  # Удаляем локальный файл
    
    return jsonify(analysis_result)

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
