from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Настройки API
VISION_API_KEY = "YOUR_AZURE_VISION_KEY"
VISION_ENDPOINT = "https://your-computer-vision-instance.cognitiveservices.azure.com/"
OPENAI_API_KEY = "YOUR_AZURE_OPENAI_KEY"
OPENAI_ENDPOINT = "https://your-openai-instance.openai.azure.com/"

# Обработка изображений
def analyze_image(image_url):
    headers = {"Ocp-Apim-Subscription-Key": VISION_API_KEY}
    data = {"url": image_url}
    response = requests.post(f"{VISION_ENDPOINT}/vision/v3.2/analyze?visualFeatures=Tags", json=data, headers=headers)
    return response.json()

# Получение рецепта
def generate_recipe(ingredients):
    prompt = f"Generate a recipe using these ingredients: {', '.join(ingredients)}"
    headers = {
        "Content-Type": "application/json",
        "api-key": OPENAI_API_KEY
    }
    data = {"prompt": prompt, "max_tokens": 100}
    response = requests.post(f"{OPENAI_ENDPOINT}/openai/deployments/text-davinci/completions", json=data, headers=headers)
    return response.json()

@app.route("/upload", methods=["POST"])
def upload_image():
    file = request.files["image"]
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)

    # Анализ изображения
    tags = analyze_image(file_path)
    ingredients = [tag["name"] for tag in tags["tags"] if tag["confidence"] > 0.7]

    # Генерация рецепта
    recipe = generate_recipe(ingredients)

    return jsonify({"ingredients": ingredients, "recipe": recipe["choices"][0]["text"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
