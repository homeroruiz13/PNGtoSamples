import os
import fitz  # PyMuPDF for PDF manipulation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageEnhance
import tempfile
import shutil

# Define the correct footer file path
FOOTER_DIR = "/Users/homeroruiz/Downloads/Compound/LemonPark/"

# Define horizontal extension in points (convert from pixels to points)
# 1 point = 1/72 inch, assuming standard 72 DPI
# 8.5039 pixels at 72 DPI = approximately 8.5039 points
HORIZONTAL_EXTENSION_POINTS = 8.5039

def enhance_image(image_path, contrast=1.2, brightness=1.1, sharpness=1.3):
    """
    Enhance image quality with adjustable parameters
    """
    img = Image.open(image_path).convert("RGB")
    
    # Apply enhancements
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    
    # Save enhanced image to a temporary file
    temp_path = f"temp_enhanced_{os.path.basename(image_path)}"
    img.save(temp_path, format="PNG", quality=100, dpi=(600, 600))
    
    return temp_path

def create_pdf(image_path, height_ft, label, width_ft=2, dpi=1200, double_blade=False, spacing_points=20, design_name=None):
    """
    Create a tiled large-format PDF from an image, then overlay the correct footer at the bottom.
    Adds the design_name (or image filename if not provided) to the footer.
    """
    try:
        # Enhance the image first
        enhanced_image_path = enhance_image(image_path)
        
        # Convert feet to points (1 inch = 72 points, 1 foot = 12 inches)
        tile_width_points = width_ft * 12 * 72
        total_height_points = height_ft * 12 * 72
        
        # Add horizontal extension to each side (increasing tile width)
        extended_tile_width = tile_width_points + (2 * HORIZONTAL_EXTENSION_POINTS)
        
        if double_blade:
            # For double blade, we extend both tiles and maintain the spacing
            total_width_points = 2 * extended_tile_width + spacing_points
            output_pdf = f"temp_{height_ft}ft_{label}_DoubleBlade.pdf"
        else:
            total_width_points = extended_tile_width
            output_pdf = f"temp_{height_ft}ft_{label}.pdf"

        # Open the enhanced image
        img = Image.open(enhanced_image_path).convert("RGB")
        img_width, img_height = img.size
        
        # Calculate scaling factor based on the extended tile width to eliminate white space
        # This ensures the image is scaled to fill the entire extended width
        scale_factor = extended_tile_width / img_width
        new_width = int(extended_tile_width)  # Convert to integer for PIL
        new_height = int(img_height * scale_factor)
        
        # Resize image using high-quality resampling
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save the resized image with high quality settings
        temp_resized = f"temp_resized_{os.path.basename(image_path)}"
        img.save(temp_resized, format="PNG", quality=100, dpi=(dpi, dpi))

        # Calculate the number of times the image should be repeated vertically
        tile_count = (total_height_points // new_height) + 1

        # Create PDF with high DPI, using the extended width
        c = canvas.Canvas(output_pdf, pagesize=(total_width_points, total_height_points))
        c.setAuthor("Automated PDF Generator")
        c.setTitle(f"{label} {height_ft}ft {'Double Blade' if double_blade else ''}")
        c.setSubject(f"High-Quality Print for {design_name or os.path.basename(image_path)}")
        c.setKeywords(["large format", "high quality", "print"])

        # Use ImageReader for better quality rendering
        img_reader = ImageReader(temp_resized)
        
        y_position = 0
        for _ in range(tile_count):
            # Draw with best quality settings available
            # Place image at the edge (no x_offset needed since image is already sized correctly)
            c.drawImage(img_reader, 0, y_position, width=new_width, height=new_height, 
                        preserveAspectRatio=True, mask='auto')
            
            if double_blade:
                # For double blade, place the second image with proper spacing
                second_image_x = extended_tile_width + spacing_points
                c.drawImage(img_reader, second_image_x, y_position, 
                           width=new_width, height=new_height, 
                           preserveAspectRatio=True, mask='auto')
                
            y_position += new_height  # Move up for the next tile

        # Set PDF metadata for better quality printing
        # Note: Using highest quality settings available in ReportLab
        c.showPage()
        c.save()
        
        print(f"Temporary PDF saved to {output_pdf}")

        # Get design name (if not provided, use the image filename without path and extension)
        if design_name is None:
            design_name = os.path.splitext(os.path.basename(image_path))[0]
            
        # Overlay footer at the bottom with design name
        overlay_footer(output_pdf, height_ft, label, double_blade, spacing_points, design_name)
        
        # Clean up temporary files
        os.remove(enhanced_image_path)
        os.remove(temp_resized)

    except Exception as e:
        print(f"Error: {e}")

def overlay_footer(base_pdf_path, height_ft, label, double_blade=False, spacing_points=20, design_name=None):
    """
    Fully overlay the footer(s) onto the generated base PDF at the very bottom,
    and add the image name text next to "design" in Arial font.
    """
    try:
        # Select the correct footer file based on height and label
        footer_files = {
            (13, "TRAD"): os.path.join(FOOTER_DIR, "Footer_13ft_TRAD.pdf"),
            (27, "TRAD"): os.path.join(FOOTER_DIR, "Footer_27ft_TRAD.pdf"),
            (13, "P&S"): os.path.join(FOOTER_DIR, "Footer_13ft_P&S.pdf"),
            (27, "P&S"): os.path.join(FOOTER_DIR, "Footer_27ft_P&S.pdf"),
        }

        footer_pdf_path = footer_files.get((height_ft, label))
        if not footer_pdf_path or not os.path.exists(footer_pdf_path):
            print(f"Error: Footer file not found for {height_ft}ft {label} at {footer_pdf_path}")
            return

        # Open base PDF and footer PDF
        base_pdf = fitz.open(base_pdf_path)
        footer_pdf = fitz.open(footer_pdf_path)

        # Extract footer as a high-resolution image to preserve quality
        footer_page = footer_pdf[0]
        footer_pixmap = footer_page.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False)  # 3x resolution
        footer_image_path = f"footer_{height_ft}_{label}.png"
        footer_pixmap.save(footer_image_path, output="png")

        # Use provided design_name or extract from file path if not provided
        if design_name is None:
            design_name = os.path.splitext(os.path.basename(base_pdf_path))[0]
            # Remove the temp_ prefix and format info for cleaner display
            design_name = design_name.replace("temp_", "").split("_")[0]

        for page_num in range(len(base_pdf)):
            base_page = base_pdf[page_num]
            base_rect = base_page.rect

            # Calculate extended tile width
            extended_tile_width = (base_rect.width - spacing_points) / 2 if double_blade else base_rect.width
            
            # Calculate the width for the footer (should match the image width without overlay issues)
            footer_width = extended_tile_width
            footer_height = footer_pixmap.height * (footer_width / footer_pixmap.width)  # Maintain aspect ratio

            # Place footer at the very bottom of the page
            y1 = base_rect.height  # Bottom of the page
            y0 = y1 - footer_height  # Top of the footer

            # Overlay single footer for standard PDFs
            if not double_blade:
                # Place footer at the same position as the image (no offset)
                base_page.insert_image(fitz.Rect(0, y0, footer_width, y1), 
                                     filename=footer_image_path)
                
                # Add design name text - position set to match the "design" text in footer
                text_x = footer_width * 0.77
                text_y = y1 - footer_height * 0.54  # Adjusted for better positioning
                add_text_to_page(base_page, design_name, text_x, text_y, fontsize=12)
                
            else:
                # For double-blade PDFs, overlay two footers on each tile with proper spacing
                left_x = 0
                right_x = extended_tile_width + spacing_points
                
                base_page.insert_image(fitz.Rect(left_x, y0, left_x + footer_width, y1), 
                                      filename=footer_image_path)
                base_page.insert_image(fitz.Rect(right_x, y0, right_x + footer_width, y1), 
                                      filename=footer_image_path)
                
                # Add design name text on both footers
                text_x_left = left_x + footer_width * 0.77
                text_x_right = right_x + footer_width * 0.77
                text_y = y1 - footer_height * 0.53  # Slightly adjusted
                
                add_text_to_page(base_page, design_name, text_x_left, text_y, fontsize=12)
                add_text_to_page(base_page, design_name, text_x_right, text_y, fontsize=12)

        # Save the final PDF with footer applied
        final_pdf_path = base_pdf_path.replace("temp_", "")
        
        # Save with higher quality settings
        base_pdf.save(final_pdf_path, 
                     garbage=4,        # Maximum garbage collection
                     deflate=False,    # No deflate compression
                     clean=True)       # Clean unused objects
        
        base_pdf.close()
        footer_pdf.close()

        # Cleanup temporary footer image
        os.remove(footer_image_path)

        print(f"Final PDF with footer saved as {final_pdf_path}")

        # Clean up temporary file
        os.remove(base_pdf_path)

    except Exception as e:
        print(f"Error overlaying footer: {e}")
        
def add_text_to_page(page, text, x, y, fontname="Arial", fontsize=12):
    """
    Add text to a PDF page at specific coordinates using Arial font.
    """
    try:
        # Create text writer with specified font
        tw = fitz.TextWriter(page.rect)
        
        # Load the Arial font (or fallback to Helvetica if Arial isn't available)
        font = None
        try:
            font = fitz.Font(fontname)
        except:
            font = fitz.Font("helv")  # Helvetica as fallback
            print(f"Warning: Arial font not available, using Helvetica instead")
        
        # Add text with specified properties
        tw.append((x, y), text, font=font, fontsize=fontsize)
        
        # Write the text to the page with better rendering quality
        tw.write_text(page, color=(0, 0, 0))  # Black text for better readability
        
    except Exception as e:
        print(f"Error adding text to page: {e}")

if __name__ == "__main__":
    image_path = input("Enter the full path to the image file: ").strip()

    if not os.path.exists(image_path):
        print(f"Error: The specified image file '{image_path}' does not exist.")
    else:
        # Use the image filename as the design name
        design_name = os.path.splitext(os.path.basename(image_path))[0]
            
        for label in ["P&S", "TRAD"]:
            for height in [13, 27]:
                create_pdf(image_path, height_ft=height, label=label, design_name=design_name)
                create_pdf(image_path, height_ft=height, label=label, double_blade=True, design_name=design_name)
