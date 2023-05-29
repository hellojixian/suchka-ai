#!/usr/bin/env python3
import cv2
import sys

def extract_faces(image_path):
    # Load the pre-trained face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Load the image
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Perform face detection
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Extract faces
    extracted_faces = []
    padding = 0
    for (x, y, w, h) in faces:
      padding_y = int(h * padding)
      padding_x = int(w * padding)
      face = image[y-padding_y:y+h+padding_y, x-padding_x:x+w+padding_x]
      extracted_faces.append(face)

    return extracted_faces

# read image path from command line
image_path = sys.argv[1]
faces = extract_faces(image_path)
# Saving the extracted faces
for i, face in enumerate(faces):
  out_path = f'{sys.argv[2]}/extracted_face_{i}.jpg'
  print(i, out_path)
  cv2.imwrite(out_path, face)