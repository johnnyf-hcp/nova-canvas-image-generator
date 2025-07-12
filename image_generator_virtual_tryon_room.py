#!/usr/bin/env python3
import boto3
import json
import base64
import os
import subprocess
from datetime import datetime

# Constants
NUMBER_OF_IMAGES = 3

def encode_image(image_path):
    """Encode image file to base64"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading image {image_path}: {str(e)}")
        return None

def generate_virtual_tryon(room_image_path, furniture_image_path, prompt_text):
    """Generate virtual try-on using Bedrock Nova Canvas"""
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Encode images
    room_image = encode_image(room_image_path)
    furniture_image = encode_image(furniture_image_path)
    
    if not room_image or not furniture_image:
        return None
    
    body = {
        "taskType": "VIRTUAL_TRY_ON",
        "virtualTryOnParams": {
            "sourceImage": room_image,
            "referenceImage": furniture_image,
            "maskType": "PROMPT",
            "promptBasedMask":{
                "maskShape": "DEFAULT",
                "maskPrompt": prompt_text,
            },
        },
        "imageGenerationConfig": {
            "numberOfImages": NUMBER_OF_IMAGES, # number of images to generate
            #"seed": 12, # Initial noise setting. Default 12.
            "quality": "standard" # standard or premium
        }
    }

    body_json = json.dumps(body, indent = 2)
    try:
        response = bedrock.invoke_model(
            modelId='amazon.nova-canvas-v1:0',
            body=body_json,
            accept="application/json",
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        print(len(response_body['images']))
        if 'images' in response_body and len(response_body['images']) > 0:
            return response_body['images']
        else:
            print("No image generated in response")
            return None
            
    except Exception as e:
        print(f"Error generating virtual try-on: {str(e)}")
        return None

def save_and_open_images(images_data):
    """Save image to file and open it"""

    for index, image_data in enumerate(images_data):
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"virtual_tryon_{timestamp}_{index}.png"
            filepath = os.path.join(os.getcwd(), filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            print(f"\nImage saved as: {filename}")
            
            # Open image (macOS)
            subprocess.run(['open', filepath])
            
            if filepath:
                print(f"🖼️  Image opened for viewing: {filepath}")
            
        except Exception as e:
            print(f"Error saving/opening image: {str(e)}")
            return None

def main():
    print("👗 Bedrock Nova Canvas Virtual Try-On")
    print("=" * 40)
    
    # Get person image path
    room_image = input("\nEnter path to room image: ").strip()
    if not room_image or not os.path.exists(room_image):
        print("Room image file not found!")
        return
    
    # Get garment image path
    furniture_image = input("Enter path to furniture image: ").strip()
    if not furniture_image or not os.path.exists(furniture_image):
        print("Furniture image file not found!")
        return

    # Get user prompt
    prompt_text = input("Enter furniture change instructions (E.g. replace sofa): ").strip()
    if not prompt_text.strip():
        prompt_text = "replace sofa"

    print(f"\nGenerating virtual try-on...")
    print(f"Person: {os.path.basename(room_image)}")
    print(f"Garment: {os.path.basename(furniture_image)}")
    print(f"Instructions: {prompt_text}")
    print("Please wait...")
    
    # Generate virtual try-on
    images_data = generate_virtual_tryon(room_image, furniture_image, prompt_text)
    
    if images_data:
        print("✅ Virtual try-on generated successfully!")
        save_and_open_images(images_data)

    else:
        print("❌ Failed to generate virtual try-on")

if __name__ == "__main__":
    main()