from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
CORS(app)  # Включение CORS

# Настройки API
VISION_API_KEY = os.getenv("VISION_API_KEY")
VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")

# Создание папки для загрузок
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Обработка изображений
def analyze_image(image_url):
    headers = {"Ocp-Apim-Subscription-Key": VISION_API_KEY}
    data = {"url": image_url}
    response = requests.post(
        f"{VISION_ENDPOINT}/vision/v3.2/analyze?visualFeatures=Tags",
        json=data,
        headers=headers,
    )
    return response.json()

# Генерация рецепта
def generate_recipe(ingredients):
    prompt = f"Generate a recipe using these ingredients: {', '.join(ingredients)}"
    headers = {
        "Content-Type": "application/json",
        "api-key": OPENAI_API_KEY,
    }
    data = {"prompt": prompt, "max_tokens": 100}
    response = requests.post(
        f"{OPENAI_ENDPOINT}/openai/deployments/text-davinci/completions",
        json=data,
        headers=headers,
    )
    return response.json()

# Маршрут для загрузки изображения
@app.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Анализ изображения
    try:
        tags = analyze_image(file_path)
        ingredients = [tag["name"] for tag in tags["tags"] if tag["confidence"] > 0.7]

        # Генерация рецепта
        recipe = generate_recipe(ingredients)

        return jsonify({"ingredients": ingredients, "recipe": recipe["choices"][0]["text"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
