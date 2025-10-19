from PIL import Image
import os

# Define the folder containing the .webp images
folder_path = './'  # Replace with the actual path to your folder

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".webp"):
        # Create the full path to the image
        webp_image_path = os.path.join(folder_path, filename)
        
        # Open the .webp image
        with Image.open(webp_image_path) as img:
            # Define the output PNG file path
            png_image_path = os.path.splitext(webp_image_path)[0] + '.png'
            
            # Save the image as PNG
            img.save(png_image_path, 'PNG')

        print(f"Converted {filename} to PNG")

print("Conversion complete!")
