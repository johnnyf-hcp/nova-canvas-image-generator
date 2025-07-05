#!/usr/bin/env python3
import boto3
import json
import base64
import os
import subprocess
from datetime import datetime

def get_garment_class():
    """Display menu and get user's garment class choice"""
    garments = {
        '1': 'UPPER_BODY',
        '2': 'LOWER_BODY',
        '3': 'FOOTWEAR',
        '4': 'FULL_BODY'
    }
    
    print("\nSelect garment class:")
    print("1. Upper Body (shirts, jackets, etc.)")
    print("2. Lower Body (pants, skirts, etc.)")
    print("3. Footwear")
    print("4. Full Body (jumpsuits, etc.)")
    
    while True:
        garment_choice = input("\nEnter your choice (1-4): ").strip()
        if garment_choice in garments:
            return garments[garment_choice]
        print("Invalid choice. Please enter a number between 1-4.")

def encode_image(image_path):
    """Encode image file to base64"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading image {image_path}: {str(e)}")
        return None

def generate_virtual_tryon(person_image_path, garment_image_path, garment_class, styling_cues=None, image_stitching=True):
    """Generate virtual try-on using Bedrock Nova Canvas"""
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Encode images
    person_image = encode_image(person_image_path)
    garment_image = encode_image(garment_image_path)
    
    if not person_image or not garment_image:
        return None
    
    body = {
        "taskType": "VIRTUAL_TRY_ON",
        "virtualTryOnParams": {
            "sourceImage": person_image,
            "referenceImage": garment_image,
            "maskType": "GARMENT",
            "garmentBasedMask": {"garmentClass": garment_class}
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "standard"
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
            return response_body['images'][0]
        else:
            print("No image generated in response")
            return None
            
    except Exception as e:
        print(f"Error generating virtual try-on: {str(e)}")
        return None

def save_and_open_image(image_data):
    """Save image to file and open it"""
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"virtual_tryon_{timestamp}.png"
        filepath = os.path.join(os.getcwd(), filename)
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        print(f"\nImage saved as: {filename}")
        
        # Open image (macOS)
        subprocess.run(['open', filepath])
        
        return filepath
        
    except Exception as e:
        print(f"Error saving/opening image: {str(e)}")
        return None

def main():
    print("👗 Bedrock Nova Canvas Virtual Try-On")
    print("=" * 40)
    
    # Get person image path
    person_image = input("\nEnter path to person image: ").strip()
    if not person_image or not os.path.exists(person_image):
        print("Person image file not found!")
        return
    
    # Get garment image path
    garment_image = input("Enter path to garment image: ").strip()
    if not garment_image or not os.path.exists(garment_image):
        print("Garment image file not found!")
        return
    
    # Get garment class
    garment_class = get_garment_class()
        
    print(f"\nGenerating virtual try-on...")
    print(f"Person: {os.path.basename(person_image)}")
    print(f"Garment: {os.path.basename(garment_image)}")
    print(f"Class: {garment_class}")
    print("Please wait...")
    
    # Generate virtual try-on
    image_data = generate_virtual_tryon(person_image, garment_image, garment_class)
    
    if image_data:
        print("✅ Virtual try-on generated successfully!")
        filepath = save_and_open_image(image_data)
        if filepath:
            print("🖼️  Image opened for viewing!")
    else:
        print("❌ Failed to generate virtual try-on")

if __name__ == "__main__":
    main()