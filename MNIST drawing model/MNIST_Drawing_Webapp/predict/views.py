import base64
import io
import numpy as np
from django.shortcuts import render
from django.http import JsonResponse
from PIL import Image, ImageOps
import tensorflow as tf
import json
from django.views.decorators.csrf import csrf_exempt

# Ensure the model path is formatted correctly
MODEL_PATH = r'C:\GitHubRepositories\General-Projects\MNIST drawing model\Model_files\mnist_model.h5'
model = tf.keras.models.load_model(MODEL_PATH, compile=False)  # Load the model once globally


def index(request):
    return render(request, 'predict/index.html')


@csrf_exempt
def predict_digit(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            print("Received data:", data)
            img_data = data.get('image')

            if not img_data:
                return JsonResponse({"error": "No image data found"}, status=400)

            # Decode base64 image data
            format, imgstr = img_data.split(';base64,')
            img_bytes = base64.b64decode(imgstr)

            # Save decoded image directly to inspect it
            with open("decoded_image.png", "wb") as f:
                f.write(img_bytes)

            # Load and process the image
            image = Image.open(io.BytesIO(img_bytes))
            print("Image mode:", image.mode)

            # Force white background if necessary
            if image.mode == 'RGBA':
                background = Image.new("RGBA", image.size, "WHITE")
                image = Image.alpha_composite(background, image).convert('L')
            else:
                image = image.convert('L')  # Convert to grayscale if not RGBA

            # Save original and resized image for inspection
            image.save("original_received_image.png")
            image = image.resize((28, 28))
            image.save("resized_image.png")

            # Convert to array and print values
            image_array = tf.keras.preprocessing.image.img_to_array(image)

            # Normalize and reshape
            image_array = image_array / 255.0
            image_array = image_array.reshape(1, 784)

            # Predict using the model and get raw logits
            logits = model.predict(image_array)  # Use image_array instead of image

            # Apply softmax to get probabilities
            probabilities = tf.nn.softmax(logits).numpy() * 100

            print("Prediction array:", probabilities)
            predicted_digit = tf.argmax(probabilities, axis=1).numpy()[0]

            return JsonResponse({"prediction": int(predicted_digit)})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print("Error during prediction:", e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)
