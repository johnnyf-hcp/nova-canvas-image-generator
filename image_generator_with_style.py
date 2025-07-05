#!/usr/bin/env python3
import boto3
import json
import base64
import os
import subprocess
from datetime import datetime

def get_visual_style():
    """Display menu and get user's visual style choice"""
    styles = {
        '1': '3D_ANIMATED_FAMILY_FILM',
        '2': 'DESIGN_SKETCH',
        '3': 'FLAT_VECTOR_ILLUSTRATION',
        '4': 'GRAPHIC_NOVEL_ILLUSTRATION',
        '5': 'MAXIMALISM',
        '6': 'MIDCENTURY_RETRO',
        '7': 'PHOTOREALISM',
        '8': 'SOFT_DIGITAL_PAINTING'
    }
    
    print("\nSelect a visual style:")
    print("1. 3D Animated Family Film")
    print("2. Design Sketch")
    print("3. Flat Vector Illustration")
    print("4. Graphic Novel Illustration")
    print("5. Maximalism")
    print("6. Midcentury Retro")
    print("7. Photorealism")
    print("8. Soft Digital Painting")
    
    while True:
        choice = input("\nEnter your choice (1-8): ").strip()
        if choice in styles:
            return styles[choice]
        print("Invalid choice. Please enter a number between 1-8.")

def generate_image(prompt, style):
    """Generate image using Bedrock Nova Canvas"""
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": prompt,
            "style": ""
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "standard",
            "height": 1024,
            "width": 1024,
            "cfgScale": 8.0,
            "seed": 42
        }
    }
    
    # Add style if specified
    if style != 'none':
        body["textToImageParams"]["text"] = f"{prompt}"
        body["textToImageParams"]["style"] = f"{style}"
    
    try:
        print(body)
        response = bedrock.invoke_model(
            modelId='amazon.nova-canvas-v1:0',
            body=json.dumps(body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'images' in response_body and len(response_body['images']) > 0:
            return response_body['images'][0]
        else:
            print("No image generated in response")
            return None
            
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return None

def save_and_open_image(image_data):
    """Save image to file and open it"""
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_image_{timestamp}.png"
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
    print("🎨 Bedrock Nova Canvas Image Generator")
    print("=" * 40)
    
    # Get user prompt
    prompt = input("\nEnter your image prompt: ").strip()
    if not prompt:
        print("Prompt cannot be empty!")
        return
    
    # Get visual style
    style = get_visual_style()
    
    print(f"\nGenerating image with prompt: '{prompt}'")
    print(f"Visual style: {style}")
    print("Please wait...")
    
    # Generate image
    image_data = generate_image(prompt, style)
    
    if image_data:
        print("✅ Image generated successfully!")
        filepath = save_and_open_image(image_data)
        if filepath:
            print("🖼️  Image opened for viewing!")
    else:
        print("❌ Failed to generate image")

if __name__ == "__main__":
    main()