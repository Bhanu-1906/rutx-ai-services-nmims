
import numpy as np
import cv2
import time
import logging
import os
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image
from PIL import ImageDraw
import onnxruntime as ort
from yolo_onnx.yolov8_onnx import YOLOv8
from collections import Counter
 
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
 
class PlanogramAnalyzer:
    """
    A comprehensive planogram analysis system that combines YOLO detection
    with ResNet classification for retail product identification.
    """
   
    def __init__(self, yolo_model_path: str, resnet_model_path: str,
                 detection_size: int = 640, conf_threshold: float = 0.4,
                 iou_threshold: float = 0.5, classification_threshold: float = 0.85):
        self.detection_size = detection_size
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.classification_threshold = classification_threshold
        self.yolo_detector = None
        self.resnet_session = None
        self.yolo_model_path = yolo_model_path
        self.resnet_model_path = resnet_model_path
       
        # Class names mapping - sorted like in Gradio version
        # self.class_names = sorted([
        #     'Doritos_Blue', 'Doritos_Purple', 'Doritos_Red',
        #     'Dove_Soap_Blue', 'Dove_Soap_Blue_2', 'Dove_Soap_Brown',
        #     'Dove_Soap_Coconut', 'Dove_Soap_Green', 'Dove_Soap_Pink',
        #     'Dove_Soap_Pink_2', 'Dove_Soap_Yellow', 'Nivea_blue_lotion', 'unknown'
        # ])
        
        self.class_names = sorted(["Competitor","Marlboro Gold","Marlboro Red","Marlboro Green"])
        # Create index mapping for class names
        self.class_name_to_idx = {name: idx for idx, name in enumerate(self.class_names)}
       
        # Load models
        # self._load_models(yolo_model_path, resnet_model_path)
        logger.info("PlanogramAnalyzer initialized successfully")
   
    async def initialize(self):
        if self.yolo_model_path is None or self.resnet_model_path is None:
            logger.error("Model paths not provided")
            raise ValueError("Model paths not provided")
            
        # Check if models exist with simple error handling
        if not os.path.exists(self.yolo_model_path):
            logger.error(f"YOLO model not found at: {self.yolo_model_path}")
            raise FileNotFoundError(f"YOLO model not found at: {self.yolo_model_path}")
            
        if not os.path.exists(self.resnet_model_path):
            logger.error(f"ResNet model not found at: {self.resnet_model_path}")
            raise FileNotFoundError(f"ResNet model not found at: {self.resnet_model_path}")
            
        # Load models
        await self._load_models()
 
    async def _load_models(self) -> None:
        """Load YOLO and ResNet models."""
        try:
            # Load YOLO model with simplified error handling
            try:
                self.yolo_detector = YOLOv8(self.yolo_model_path)
            except Exception as yolo_error:
                logger.error(f"Failed to load YOLO model: {yolo_error}")
                raise RuntimeError(f"Failed to load YOLO model: {yolo_error}") from yolo_error
           
            # Load ResNet model with simplified settings
            try:
                providers = ['CPUExecutionProvider']
                
                # Use default session options for better compatibility
                self.resnet_session = ort.InferenceSession(
                    self.resnet_model_path,
                    providers=providers
                )
            except Exception as resnet_error:
                logger.error(f"Failed to load ResNet model: {resnet_error}")
                raise RuntimeError(f"Failed to load ResNet model: {resnet_error}") from resnet_error
           
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise RuntimeError("Failed to load models") from e
   

   
    async def load_and_resize_image(self, original_image: Image.Image) -> Tuple[Image.Image, Image.Image]:
        """
        Load and resize image for processing.
       
        Args:
            image_path: Path to the image file
           
        Returns:
            Tuple of (original_image, resized_image)
        """
        try:
            # original_image = Image.open(image_path)
           
            if original_image.mode != 'RGB':
                print("Different channels")
                original_image = original_image.convert('RGB')
                print("Image got converted to RGB")
            else:
                print("3 channels")
            resized_image = original_image.resize(
                (self.detection_size, self.detection_size),
                Image.Resampling.LANCZOS
            )
            logger.info(f"Image loaded and resized: {original_image.size} -> {resized_image.size}")
            return original_image, resized_image
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            raise RuntimeError("Failed to load image") from e
   
    async def detect_objects(self, image: Image.Image) -> List[Dict]:
        """
        Detect objects using YOLO model.
       
        Args:
            image: PIL Image for detection
           
        Returns:
            List of detection results
        """
        try:
            detections = self.yolo_detector(
                image,
                size=self.detection_size,
                conf_thres=self.conf_threshold,
                iou_thres=self.iou_threshold
            )
            logger.info("YOLO Detections completed")
            return detections
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            raise
   
    async def crop_detected_objects(self, original_image: Image.Image,
                            detections: List[Dict]) -> Tuple[List[Image.Image], List[List[int]]]:
        """
        Crop detected objects from the original image.
       
        Args:
            original_image: Original PIL Image
            detections: List of YOLO detections
           
        Returns:
            Tuple of (cropped_images, coordinates)
        """
        try:
            original_np = np.array(original_image)
            orig_w, orig_h = original_image.size
            scale_x = orig_w / self.detection_size
            scale_y = orig_h / self.detection_size
           
            cropped_images = []
            coordinates = []
           
            for det in detections:
                x1, y1, x2, y2 = map(int, det['bbox'])
               
                # Scale coordinates back to original image size
                x1 = max(0, int(x1 * scale_x))
                y1 = max(0, int(y1 * scale_y))
                x2 = min(orig_w, int(x2 * scale_x))
                y2 = min(orig_h, int(y2 * scale_y))
               
                # Ensure valid crop dimensions
                if x2 > x1 and y2 > y1:
                    cropped_region = original_np[y1:y2, x1:x2]
                    if cropped_region.size > 0:
                        cropped_images.append(Image.fromarray(cropped_region))
                        coordinates.append([x1, y1, x2, y2])
           
            logger.info(f"Cropped {len(cropped_images)} objects from detections")
            return cropped_images, coordinates
        except Exception as e:
            logger.error(f"Error cropping objects: {e}")
            raise
   
    async def preprocess_for_resnet(self, image: Image.Image) -> np.ndarray:
        """
        Preprocess image for ResNet classification using EXACT same preprocessing as Gradio.
        This is the key fix - using the same preprocessing as tensorflow.keras.applications.resnet50.preprocess_input
       
        Args:
            image: PIL Image to preprocess
           
        Returns:
            Preprocessed numpy array
        """
        try:
            # EXACT same preprocessing as Gradio version
            # Resize to 256x256 and convert to RGB (matching Gradio version)
            img = image.resize((256, 256)).convert("RGB")
            img_array = np.array(img, dtype=np.float32)
           
            # Apply the EXACT same preprocessing as tensorflow.keras.applications.resnet50.preprocess_input
            # This uses 'caffe' mode: will convert the images from RGB to BGR, then will zero-center each color channel
            # with respect to the ImageNet dataset, without scaling.
           
            # Convert RGB to BGR
            img_array = img_array[..., ::-1]  # RGB to BGR
           
            # Zero-center by mean pixel values from ImageNet (BGR order)
            # These are the exact values used by keras.applications.resnet50.preprocess_input
            mean = np.array([103.939, 116.779, 123.68], dtype=np.float32)
            img_array = img_array - mean
           
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
           
            # Ensure the final array is float32
            img_array = img_array.astype(np.float32)
           
            logger.debug(f"Preprocessed image shape: {img_array.shape}, dtype: {img_array.dtype}")
           
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
   
           
    async def classify_products(self, cropped_images: List[Image.Image]) -> Tuple[List[str], List[float]]:
        """
        Classify cropped product images using ResNet.
        Fixed version matching Gradio logic exactly, but without entropy.
       
        Args:
            cropped_images: List of cropped PIL Images
           
        Returns:
            Tuple of (predicted_classes, confidences)
        """
        try:
            predicted_classes = []
            confidences = []
           
            if not cropped_images:
                logger.warning("No cropped images provided for classification")
                return predicted_classes, confidences
           
            logger.info("Starting classification process")
           
            # Get input details from ONNX model
            input_name = self.resnet_session.get_inputs()[0].name
            input_shape = self.resnet_session.get_inputs()[0].shape
            logger.info(f"ONNX model input name: {input_name}, shape: {input_shape}")
           
            # Process each image
            for i, img in enumerate(cropped_images):
                try:
                    # Preprocess image with EXACT same preprocessing as Gradio
                    img_array = await self.preprocess_for_resnet(img)
                    logger.debug(f"Processing image {i+1}/{len(cropped_images)}, shape: {img_array.shape}, dtype: {img_array.dtype}")
                   
                    # Run inference
                    outputs = self.resnet_session.run(None, {input_name: img_array})
                    predictions = outputs[0][0]  # Get first (and only) batch element
                   
                    # Convert to numpy array and ensure float32
                    predictions = np.array(predictions, dtype=np.float32)
                   
                    # Ensure predictions is 1D array
                    if len(predictions.shape) > 1:
                        predictions = predictions.flatten()
                   
                    # IMPORTANT: Check if the model output is already probabilities (softmax applied)
                    # or if we need to apply softmax. Most ONNX models output raw logits.
                   
                    # Check if values are already probabilities (sum close to 1 and all positive)
                    if np.all(predictions >= 0) and np.abs(np.sum(predictions) - 1.0) < 0.01:
                        # Already probabilities
                        probabilities = predictions
                    else:
                        # Apply softmax to convert logits to probabilities
                        exp_predictions = np.exp(predictions - np.max(predictions))  # Subtract max for numerical stability
                        probabilities = exp_predictions / np.sum(exp_predictions)
                   
                    # Get the prediction results
                    max_confidence = np.max(probabilities)
                   
                    predicted_class_idx = np.argmax(probabilities)
                   
                    # Ensure predicted_class_idx is within bounds
                    if predicted_class_idx >= len(self.class_names):
                        logger.warning(f"Predicted class index {predicted_class_idx} exceeds class names length {len(self.class_names)}")
                        predicted_class_idx = len(self.class_names) - 1  # Default to last class (unknown)
                   
                    # Apply EXACT same classification logic as Gradio version
                    predicted_class_name = self.class_names[predicted_class_idx]
                    # EXACT same logic as Gradio:
                    # 1. First check if it's unknown class
                    if predicted_class_name == 'Competitor':
                        final_class = "Competitor Product"
                    # 2. Then check confidence threshold
                    elif max_confidence < self.classification_threshold:
                        final_class = "Competitor Product"
                    else:
                        final_class = predicted_class_name
               
                    predicted_classes.append(final_class)
                    confidences.append(float(max_confidence))
                    print(max_confidence,final_class)
                   
                    logger.debug(f"Image {i+1}: Raw prediction: {predicted_class_name}, Confidence: {max_confidence:.3f}, Final: {final_class}")
                   
                except Exception as e:
                    logger.error(f"Error processing image {i+1}: {e}")
                    # Add fallback values
                    predicted_classes.append("Competitor Product")
                    confidences.append(0.0)
           
            logger.info(f"Classification completed: {len(predicted_classes)} products classified")
            return predicted_classes, confidences
           
        except Exception as e:
            logger.error(f"Error in product classification: {e}")
            raise
 
   
    async def results(self, image: Image.Image) -> Dict[str, Any]:
        try:
            # Step 1: Load and resize image
            original_image, resized_image = await self.load_and_resize_image(image)
           
            # Step 2: Detect objects
            detections = await self.detect_objects(resized_image)
           
            if not detections:
                return {
                    'total_products': 0,
                    'own_products': 0,
                    'competitor_products': 0,
                    'product_details': []
                }
           
            # Step 3: Crop detected objects
            cropped_images, coordinates = await self.crop_detected_objects(original_image, detections)
           
            # Step 4: Classify products
            predictions, confidences = await self.classify_products(cropped_images)
           
            # Clean up memory
            del original_image
            del resized_image
            del cropped_images
           
            # Compile results
            own_products = [p for p in predictions if p != "Competitor Product"]
            competitor_count = predictions.count("Competitor Product")
           
            product_details = []
            for i, (coords, prediction) in enumerate(zip(coordinates, predictions)):
                product_details.append({
                    'id': i + 1,
                    'class': prediction,
                    'coordinates': coords,
                    'is_competitor': prediction == "Competitor Product"
                })
           
            results = {
                'total_products': len(predictions),
                'own_products': len(own_products),
                'competitor_products': competitor_count,
                'own_product_list': own_products,
                'product_details': product_details
            }
           
            return results
           
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            raise
   
     
 
 
