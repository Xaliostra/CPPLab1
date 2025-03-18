from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    response.raise_for_status()  # Проверка статус кода
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
    response.raise_for_status()  # Проверка статус кода
    return response.json()

# Маршрут для загрузки изображения
@app.route("/upload", methods=["POST"])
def upload_image():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400

        file = request.files["image"]
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Валидация типа файла (пример)
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({"error": "Invalid file type"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        tags_response = analyze_image(file_path)
        if "tags" not in tags_response:
            return jsonify({"error": "Failed to analyze image"}), 500

        ingredients = [tag["name"] for tag in tags_response["tags"] if tag["confidence"] > 0.7]

        if not ingredients:
            return jsonify({"error": "No ingredients found"}), 400

        recipe_response = generate_recipe(ingredients)
        if "choices" not in recipe_response:
            return jsonify({"error": "Failed to generate recipe"}), 500

        return jsonify({"ingredients": ingredients, "recipe": recipe_response["choices"][0]["text"]})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request failed: {e}")
        return jsonify({"error": "API request failed"}), 500

    except Exception as e:
        app.logger.error(f"Error processing image: {e}")
        return jsonify({"error": "An error occurred"}), 500

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
