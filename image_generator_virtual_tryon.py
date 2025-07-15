#!/usr/bin/env python3
import boto3
import json
import base64
import os
import subprocess
from datetime import datetime
import random
import time

# Constants
DEFAULT_MODEL_ID = "amazon.nova-reel-v1:0"

def list_s3_buckets():
    """List all available S3 buckets and return as array with ordinal and S3 filepath"""
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        
        bucket_list = []
        for index, bucket in enumerate(response['Buckets'], 1):
            bucket_info = {
                'ordinal': index,
                's3_filepath': f"s3://{bucket['Name']}"
            }
            bucket_list.append(bucket_info)
        
        return bucket_list
    except Exception as e:
        print(f"Error listing S3 buckets: {str(e)}")
        return []


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
            "garmentBasedMask": {"garmentClass": garment_class},
            "mergeStyle" : "DETAILED"
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            #"seed": 12 # default seed is 12
            "quality": "standard"   # standard or premium
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

def generate_video(image_path, prompt, s3_destination_bucket, model_id=DEFAULT_MODEL_ID):
    """
    Generate a video from an input image and prompt using async invocation.
    
    Args:
        image_path (str): Path to the input image
        prompt (str): Text prompt describing the desired video
        s3_filepath (str): S3 bucket URI where the video will be stored
    """    
    # Initialize bedrock client
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Load the input image as a Base64 string
    with open(image_path, "rb") as f:
        input_image_bytes = f.read()
        input_image_base64 = base64.b64encode(input_image_bytes).decode("utf-8")

    model_input = {
        "taskType": "TEXT_VIDEO",
        "textToVideoParams": {
            "text": prompt,
            "images": [
                {
                    "format": "png",  # May be "png" or "jpeg"
                    "source": {
                        "bytes": input_image_base64
                    }
                }
            ]
        },
        "videoGenerationConfig": {
            "durationSeconds": 6,  # 6 is the only supported value currently
            "fps": 24,  # 24 is the only supported value currently
            "dimension": "1280x720",  # "1280x720" is the only supported value currently
            "seed": random.randint(
                0, 2147483648
            ),  # A random seed guarantees we'll get a different result each time this code runs
        },
    }   

    try:
        # Start the asynchronous video generation job
        invocation = bedrock_runtime.start_async_invoke(
            modelId=model_id,
            modelInput=model_input,
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": f"{s3_destination_bucket}"}},
        )

        # Store the invocation ARN
        invocation_arn = invocation["invocationArn"]

        print("✅ Video generation started successfully!")
        print(f"📋 Invocation ARN: {invocation_arn}")
        print(f"📁 Output will be saved to: {s3_destination_bucket}")
        print("⏳ Video generation is running asynchronously. Check your S3 bucket for the result.")

        return invocation_arn
            
    except Exception as e:
        print(f"Error starting video generation: {str(e)}")
        return None

def save_video(video_data):
    """Save video to file and open it"""
    try:
        # Decode base64 video
        video_bytes = base64.b64decode(video_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"virtual_tryon_video_{timestamp}.mp4"
        filepath = os.path.join(os.getcwd(), filename)
        
        # Save video
        with open(filepath, 'wb') as f:
            f.write(video_bytes)
            
        print(f"\nVideo saved as: {filename}")
        
        # Open video (macOS)
        subprocess.run(['open', filepath])
        
        return filepath
        
    except Exception as e:
        print(f"Error saving/opening video: {str(e)}")
        return None

def check_and_download_video(s3_bucket, job_no):
    """Check if video exists in S3 and download when ready"""
    s3_client = boto3.client('s3')
    bucket_name = s3_bucket.replace('s3://', '')
    key = f"{job_no}/output.mp4"
    
    print("\nChecking for completed video...")
    while True:
        try:
            # Check if file exists
            s3_client.head_object(Bucket=bucket_name, Key=key)
            
            # File exists, download it
            print("✅ Video found! Downloading...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"virtual_tryon_video_{timestamp}.mp4"
            
            s3_client.download_file(bucket_name, key, local_filename)
            print(f"📥 Video downloaded as: {local_filename}")
            return local_filename
            
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print("⏳ Video not ready yet, checking again in 10 seconds...")
                time.sleep(10)
            else:
                print(f"❌ Error checking/downloading video: {str(e)}")
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
            print(f"🖼️  Image opened for viewing! {filepath}")
    else:
        print("❌ Failed to generate virtual try-on")
    #filepath = "./virtual_tryon_20250712_150622.png"
    # Check if you want to generate a video from the image
    do_video = input("Do you want to create a video from this image? (Y/N)").strip()
    if do_video.lower() in ('y', 'yes', 'ok'):
        prompt = input("Enter a prompt describing the video motion you want: ").strip()
        # Select S3 bucket to use
        bucket_list = list_s3_buckets()
        if not bucket_list:
            print("No S3 buckets found!")
            return
            
        for bucket in bucket_list:
            print(f"{bucket['ordinal']}:\t{bucket['s3_filepath']}")
        
        while True:
            try:
                selected_ordinal = input("Enter the number of the S3 bucket you want to use: ").strip()
                selected_index = int(selected_ordinal) - 1
                if 0 <= selected_index < len(bucket_list):
                    selected_s3_filepath = bucket_list[selected_index]['s3_filepath']
                    break
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(bucket_list)}.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        print("Generating video...")
        invocation_arn = generate_video(filepath, prompt, selected_s3_filepath)
        if invocation_arn:
            print("✅ Video generation job submitted successfully!")
            print(f"📋 Job ARN: {invocation_arn}")
            print("⏳ The video is being generated asynchronously.")
            print(f"📁 Check your S3 bucket {selected_s3_filepath} for the completed video.")

            # Get the job number from the invocation ARN
            job_no = invocation_arn.split('/')[1]
            print(f"🔢 Job number: {job_no}")
            video_filename = check_and_download_video(selected_s3_filepath, job_no)
            # Open video
            subprocess.run(['open', video_filename])
        else:
            print("❌ Failed to start video generation")   


if __name__ == "__main__":
    main()
