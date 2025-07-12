# Nova Canvas Image Generator

Includes:
- a Python script that generates images using Amazon Bedrock Nova Canvas with customizable visual styles.
- a Python script that generates images using Amazon Bedrock Nova Canvas with virtual try-on.

Ref: https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Configure AWS credentials (one of the following):
   - AWS CLI: `aws configure`
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - IAM role (if running on EC2)

3. Ensure you have access to Bedrock Nova Canvas model in us-east-1 region

## Usage for Image Generator with Visual Styles

Run the script:
```bash
python image_generator_with_style.py
```

Follow the prompts to:
1. Enter your image description
2. Select a visual style from the menu
3. Wait for generation and automatic image opening

### Visual Styles Available

- 3D Animated Family Film
- Design Sketch
- Flat Vector Illustration
- Graphic Novel Illustration
- Maximalism
- Midcentury Retro
- Photorealism
- Soft Digital Painting

Generated images are saved as PNG files with timestamps in the current directory.

## Usage for Image Generator with Virtual Try-on (Person/Clothing)

Copy files to this folder:
- Image of Person
- Image of clothing to try on

Run the script:
```bash
python image_generator_virtual_tryon.py
```

Follow the prompts to:
1. Enter the name of image file - person 
2. Enter the name of image file - clothing 
3. Select a garment type from the menu
4. Wait for generation and automatic image opening

## Garment Type Available

- Upper Body
- Lower Body
- Footwear
- Full Body

Generated images are saved as PNG files with timestamps in the current directory.

## Usage for Image Generator with Virtual Try-on (Room/Furniture)

Copy files to this folder:
- Image of room with furniture to replace
- Image of new furniture to use

Run the script:
```bash
python image_generator_virtual_tryon_room.py
```

Follow the prompts to:
1. Enter the name of image file - room 
2. Enter the name of image file - furniture 
3. Enter instruction prompt - e.g. replace sofa
4. Wait for generation and automatic image opening

Generated images are saved as PNG files with timestamps in the current directory. The script currently generates three images to give a few output variants.