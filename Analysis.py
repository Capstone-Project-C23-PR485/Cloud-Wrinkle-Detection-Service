import cv2
import os
import numpy as np
import requests
import urllib.request
from keras.applications.mobilenet_v2 import preprocess_input
# from keras.models import load_model # for testing purposes
from google.cloud import storage

def get_bounding_box(image):
    # Placeholder implementation
    # Replace this with your actual bounding box calculation logic
    height, width, _ = image.shape
    xmin = int(width * 0.25)
    ymin = int(height * 0.25)
    xmax = int(width * 0.75)
    ymax = int(height * 0.75)
    return xmin, ymin, xmax, ymax

def detect_wrinkle(data, model):
    # get the image data
    file_path = data["name"]
    file_name = file_path.split("/")[1]
    bucket_name = data["bucket"]
    image_path = f"https://storage.googleapis.com/{bucket_name}/{file_path}"

    try:
        # pull the image from gcs
        req = urllib.request.urlopen(image_path)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        image = cv2.imdecode(arr, -1)  # 'load the image'
    except Exception as e:
        print(f"DEBUG : Exception when when pulling the image from gcs. Error : {e}")
        raise Exception("Error when pulling the image from gcs")
    
    try:
        # preprocess the image
        image_resized = cv2.resize(image, (224, 224))
        image_normalized = image_resized / 255.0
        image_expanded = np.expand_dims(image_normalized, axis=0)
    except Exception as e:
        print(f"DEBUG : Exception when preprocessing image. Error : {e}")
        raise Exception("Error when preprocessing the image")

    try:
        # Perform wrinkle detection using the model
        result = model.predict(image_expanded)
        confidence = result[0][0]

        if confidence > 0:
            label = 'Wrinkled'
            color = (0, 0, 255)  # BGR format for red color
        else:
            label = 'Not Wrinkled'
            color = (0, 255, 0)  # BGR format for green color
    except Exception as e:
        print(f"Exception when predicting image. Error : {e}")
        raise Exception("Error when predicting image")

    predicted_image = cv2.resize(image, (270, 280))

    # Define bounding box coordinates
    xmin, ymin, xmax, ymax = get_bounding_box(predicted_image)

    # Draw bounding box
    cv2.rectangle(predicted_image, (xmin, ymin), (xmax, ymax), color, 2)
    cv2.putText(predicted_image, label, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    try:
        post_response = post_request(file_name, confidence, label, image_path)
    except Exception as e:
        print(f"Exception when posting request. Error {e}")
        raise Exception("Error when posting request.")
    
    try:
        upload_to_gcs_response = upload_to_gcs(bucket_name, predicted_image, file_name)
    except Exception as e:
        print(f"Exception when posting request. Error {e}")
        raise Exception("Error when posting request.")\

    return post_response, upload_to_gcs_response

def upload_to_gcs(bucket_name, image_result, file_name):
    # gcs_bucket_name = 'public-picture-media-bucket'
    image_result = cv2.imwrite(f'static/{file_name}', image_result)
    destination_blob_name = f'images_result/{file_name}'
    storage_client = storage.Client(os.getenv('PROJECT_ID'))
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(f'static/{file_name}')
    os.remove(f'static/{file_name}')

def post_request(file_name, confidence, result, file_path):
    gcs_bucket_url = f"{os.getenv('BUCKET_URL')}/images_result"
    confidence = float(confidence)
    data = {
      "id": file_path,
      "data": {
          "confidence": confidence, 
          "result": result
          },
      "image": f"{gcs_bucket_url}/wrinkle/{file_name}",
      "model": "wrinkle"
    }

    response = requests.post('https://skincheckai-api-b6zefxgbfa-et.a.run.app/machine-learning/report-analyses', json=data)

    return response;

# # for testing purposes
# model = load_model('models/wrinkle_model_mobilenetv2_V2.h5')
# data = {
#     'name' : 'images_uploaded/3abb7944-9d0f-4f4f-934b-2754e471a108.jpg',
#     'bucket' : 'public-picture-media-bucket'
# }
# print(detect_wrinkle(data, model))