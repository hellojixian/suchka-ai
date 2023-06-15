import os
import cv2
import torch
import numpy as np
from facenet_pytorch import MTCNN
from core.face.vggface import VGGFace
from core.face.gender import Gender
from core.face.functions import alignment_procedure

confidence_threshold = 0.95
gender_threshold = 0.95
cropped_face_size = (224, 224)
min_face_size = 64

def load_image(img):
  if os.path.isfile(img) is not True:
      raise ValueError(f"Confirm that {img} exists")
  return cv2.imread(img)

def detect_face(img, face_detector):
  resp = []
  detected_face = None
  img_region = [0, 0, img.shape[1], img.shape[0]]

  img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # mtcnn expects RGB but OpenCV read BGR

  try:
    with torch.no_grad():
      torch.cuda.synchronize(device=face_detector.device)
      boxes, probs, points = face_detector.detect(img_rgb, landmarks=True)

  except RuntimeError as e:
    if 'CUDA error: misaligned address' in str(e):
      print("captured CUDA error: misaligned address occurred.")
    else:
      print("captured An error occurred:", e)

  if boxes is None: return resp

  detections = []
  for i, (box, probs, point) in enumerate(zip(boxes, probs, points)):
    detections.append({"box": box, "confidence": probs, "keypoints": {"left_eye": point[0], "right_eye": point[1]}})

  if len(detections) > 0:
    for detection in detections:
      x, y, x2, y2 = detection["box"]
      w = x2 - x ; h = y2 - y

      aspect_ratio = w / h
      # Calculate the new width and height based on the target size and aspect ratio
      if aspect_ratio > 1:
        edge_length = w
        x_offset = 0
        y_offset = (w - h)/ 2
      else:
        edge_length = h
        x_offset =  (h - w)/ 2
        y_offset = 0

      # Don't process small faces
      if edge_length <= min_face_size: continue

      crop_x = x - x_offset
      crop_w = crop_x + edge_length
      crop_y = y - y_offset
      crop_h = crop_y + edge_length

      # adjust the crop region to fit within the image boundaries
      if crop_x < 0:
        crop_w += np.abs(crop_x);
        crop_x = 0
      if crop_y < 0:
        crop_h += np.abs(crop_y);
        crop_y = 0
      if crop_w > img.shape[1]:
        crop_x -= (crop_w - img.shape[1])
        crop_w = img.shape[1];
      if crop_h > img.shape[0]:
        crop_y -= (crop_h - img.shape[0])
        crop_h = img.shape[0];

      # Crop the specified region
      cropped = img[int(crop_y):int(crop_h), int(crop_x):int(crop_w)]
      cropped = cv2.resize(cropped, cropped_face_size)
      detected_face = img[int(y) : int(y + h), int(x) : int(x + w)]
      img_region = [x, y, w, h]
      confidence = detection["confidence"]

      # face alignment
      keypoints = detection["keypoints"]
      left_eye = keypoints["left_eye"]
      right_eye = keypoints["right_eye"]
      try:
        detected_face = alignment_procedure(detected_face, left_eye, right_eye)
        resp.append((detected_face, img_region, confidence, cropped))
      except:
        # if alignment fails, we will drop the face
        pass

  return resp

def extract_faces(img, target_size=(224, 224), face_detector=None):
  # this is going to store a list of img itself (numpy), it region and confidence
  extracted_faces = []

  # img might be path, base64 or numpy array. Convert it to numpy whatever it is.
  if type(img).__module__ != np.__name__: img = load_image(img)

  img_region = [0, 0, img.shape[1], img.shape[0]]
  face_objs = detect_face(img, face_detector)

  if len(face_objs) == 0:
      face_objs = [(img, img_region, 0, img)]

  for current_img, current_region, confidence, cropped in face_objs:
    if current_img.shape[0] > 0 and current_img.shape[1] > 0:
      # resize and padding
      if current_img.shape[0] > 0 and current_img.shape[1] > 0:
        factor_0 = target_size[0] / current_img.shape[0]
        factor_1 = target_size[1] / current_img.shape[1]
        factor = min(factor_0, factor_1)

        try:
          dsize = (int(current_img.shape[1] * factor), int(current_img.shape[0] * factor))
          current_img = cv2.resize(current_img, dsize)
        except:
          continue

        diff_0 = target_size[0] - current_img.shape[0]
        diff_1 = target_size[1] - current_img.shape[1]
        # Put the base image in the middle of the padded image
        current_img = np.pad(
            current_img,
            (
                (diff_0 // 2, diff_0 - diff_0 // 2),
                (diff_1 // 2, diff_1 - diff_1 // 2),
                (0, 0),
            ),
            "constant",
        )

        # double check: if target image is not still the same size with target.
        if current_img.shape[0:2] != target_size:
            current_img = cv2.resize(current_img, target_size)

        img_pixels = current_img.astype(np.float32)
        # normalizing the image pixels
        img_pixels = np.expand_dims(img_pixels, axis=0)
        img_pixels /= 255  # normalize input in [0, 1]

        # int cast is for the exception - object of type 'float32' is not JSON serializable
        region_obj = {
            "x": int(current_region[0]),
            "y": int(current_region[1]),
            "w": int(current_region[2]),
            "h": int(current_region[3]),
        }

        extracted_face = [img_pixels, region_obj, confidence, cropped]
        extracted_faces.append(extracted_face)
      # extracted_faces.append([current_img, current_region, confidence])
    return extracted_faces

gender_model = None
embedding_model = None
face_detector = None

def init_models(device='cpu'):
  face_detector   = MTCNN(factor=0.5, min_face_size=min_face_size, keep_all=True, device=device)
  gender_model    = Gender(device=device)
  embedding_model = VGGFace(device=device)
  return [face_detector, gender_model, embedding_model]


def process_image(img, models = None, return_fields=None):
  [face_detector, gender_model, embedding_model] = models if models is not None else init_models()

  # use mtcnn to detect faces
  img_objs = extract_faces(img=img, face_detector=face_detector)

  resp_objs = []
  if img_objs is None or len(img_objs) == 0: return resp_objs
  for img, region, confidence, cropped in img_objs:
    resp_obj = {}

    # discard low confidence
    if confidence <= confidence_threshold: continue

    with torch.no_grad():
      # use cropeed face to extract features
      # torch_img = torch.from_numpy(cropped.astype(np.float32).transpose(2, 0, 1)).to(embedding_model.device) / 255

      # use alighed face to extract features
      torch_img = torch.from_numpy(np.squeeze(img).transpose(2, 0, 1)).to(embedding_model.device)
      features = embedding_model.features(torch_img)
      embedding = embedding_model.embedding(features).cpu().detach().numpy().tolist()
      gender_probs = gender_model(features).cpu().detach().numpy().tolist()

    # if max gender_probs is less than gender_threshold, discard
    if np.max(gender_probs) <= gender_threshold: continue

    # discard expanded dimension
    if len(img.shape) == 4:
        img = img[0]

    if return_fields and 'face' in return_fields:         resp_obj["face"] = img[:, :, ::-1]
    if return_fields and 'facial_area' in return_fields:  resp_obj["facial_area"] = region
    if return_fields and 'confidence' in return_fields:   resp_obj["confidence"] = confidence
    if return_fields and 'embedding' in return_fields:    resp_obj["embedding"] = embedding
    if return_fields and 'cropped_face' in return_fields: resp_obj["cropped_face"] = cropped
    if return_fields and 'gender' in return_fields:       resp_obj["gender"] = {gender_label: gender_probs[i] for i, gender_label in enumerate(Gender.labels)}
    resp_objs.append(resp_obj)

  return resp_objs