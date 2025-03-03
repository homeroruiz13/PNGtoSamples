from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from PIL import Image
import os

def create_large_pdf(image_path, height_ft, width_ft=2, dpi=600):
    """
    Create a tiled large-format PDF from an image, duplicating it vertically to fill the full height with improved quality.
    
    :param image_path: Path to the input image
    :param width_ft: Width of each tile in feet (fixed at 24 inches = 2 feet)
    :param height_ft: Height of the total print in feet (either 13 or 27 feet)
    :param dpi: Resolution in dots per inch (default is 600 DPI for higher quality)
    """
    # Convert feet to points (1 inch = 72 points, 1 foot = 12 inches)
    tile_width_points = width_ft * 12 * 72
    total_height_points = height_ft * 12 * 72
    
    # Generate output PDF name based on image name and height
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_pdf = f"{base_name}_{height_ft}ft.pdf"
    
    # Open the image and enhance quality
    img = Image.open(image_path)
    img = img.convert("RGB")  # Ensure compatibility
    img_width, img_height = img.size
    
    # Calculate the scaling factor to make the image exactly 24 inches wide
    scale_factor = tile_width_points / img_width
    new_width = tile_width_points  # Make the image exactly 24 inches wide
    new_height = img_height * scale_factor
    
    # Resize image to improve quality when scaled
    img = img.resize((int(new_width), int(new_height)), Image.LANCZOS)
    
    # Calculate how many times the image needs to be repeated vertically
    tile_count = int(total_height_points / new_height) + 1
    
    # Create PDF
    c = canvas.Canvas(output_pdf, pagesize=(tile_width_points, total_height_points))
    
    # Save the processed image temporarily
    temp_image_path = f"{base_name}_temp.jpg"
    img.save(temp_image_path, quality=95, dpi=(dpi, dpi))
    
    # Place the image multiple times to fill the entire height
    y_position = 0
    for _ in range(tile_count):
        c.drawImage(temp_image_path, 0, y_position, new_width, new_height, preserveAspectRatio=True, mask='auto')
        y_position += new_height  # Move up for the next tile
    
    c.showPage()
    c.save()
    
    # Remove the temporary image file
    os.remove(temp_image_path)
    
    print(f"PDF saved to {output_pdf}")

if __name__ == "__main__":
    image_path = input("Enter the path to the image file: ").strip()
    
    if not os.path.exists(image_path):
        print("Error: The specified image file does not exist.")
    else:
        # Generate both 13ft and 27ft PDFs
        create_large_pdf(image_path, height_ft=13)
        create_large_pdf(image_path, height_ft=27)
