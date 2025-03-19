from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Разрешение запросов от всех источников

# Настройки API
VISION_API_KEY = os.getenv("VISION_API_KEY")
VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")

# Логирование переменных окружения
logger.info(f"VISION_API_KEY: {VISION_API_KEY}")
logger.info(f"VISION_ENDPOINT: {VISION_ENDPOINT}")
logger.info(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
logger.info(f"OPENAI_ENDPOINT: {OPENAI_ENDPOINT}")

# Создание папки для загрузок
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Created upload folder: {UPLOAD_FOLDER}")

# Обработка изображений
def analyze_image(image_url):
    logger.info(f"Analyzing image: {image_url}")
    headers = {"Ocp-Apim-Subscription-Key": VISION_API_KEY}
    data = {"url": image_url}
    try:
        response = requests.post(
            f"{VISION_ENDPOINT}/vision/v3.2/analyze?visualFeatures=Tags",
            json=data,
            headers=headers,
        )
        response.raise_for_status()  # Проверка статус кода
        logger.info(f"Vision API response: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Vision API request failed: {e}, response: {response.text if 'response' in locals() else 'No response'}")
        raise

# Генерация рецепта
def generate_recipe(ingredients):
    logger.info(f"Generating recipe for ingredients: {ingredients}")
    prompt = f"Generate a recipe using these ingredients: {', '.join(ingredients)}"
    headers = {
        "Content-Type": "application/json",
        "api-key": OPENAI_API_KEY,
    }
    data = {"prompt": prompt, "max_tokens": 100}
    try:
        response = requests.post(
            f"{OPENAI_ENDPOINT}/openai/deployments/text-davinci/completions",
            json=data,
            headers=headers,
        )
        response.raise_for_status()  # Проверка статус кода
        logger.info(f"OpenAI API response: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI API request failed: {e}, response: {response.text if 'response' in locals() else 'No response'}")
        raise

# Маршрут для загрузки изображения
@app.route("/upload", methods=["POST"])
def upload_image():
    try:
        logger.info("Received image upload request")
        if "image" not in request.files:
            logger.warning("No image provided")
            return jsonify({"error": "No image provided"}), 400

        file = request.files["image"]
        if file.filename == '':
            logger.warning("No selected file")
            return jsonify({"error": "No selected file"}), 400

        # Валидация типа файла (пример)
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            logger.warning("Invalid file type")
            return jsonify({"error": "Invalid file type"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        logger.info(f"Saved file to: {file_path}")

        tags_response = analyze_image(file_path)
        if "tags" not in tags_response:
            logger.error("Failed to analyze image")
            return jsonify({"error": "Failed to analyze image"}), 500

        ingredients = [tag["name"] for tag in tags_response["tags"] if tag["confidence"] > 0.7]
        logger.info(f"Extracted ingredients: {ingredients}")

        if not ingredients:
            logger.warning("No ingredients found")
            return jsonify({"error": "No ingredients found"}), 400

        recipe_response = generate_recipe(ingredients)
        if "choices" not in recipe_response:
            logger.error("Failed to generate recipe")
            return jsonify({"error": "Failed to generate recipe"}), 500

        logger.info("Recipe generated successfully")
        return jsonify({"ingredients": ingredients, "recipe": recipe_response["choices"][0]["text"]})

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return jsonify({"error": "API request failed"}), 500

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return jsonify({"error": "An error occurred"}), 500

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed file: {file_path}")

# Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
