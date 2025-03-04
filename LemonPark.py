import os
import fitz  # PyMuPDF for PDF manipulation
from reportlab.pdfgen import canvas
from PIL import Image

# Define the correct footer file path
FOOTER_DIR = "/Users/homeroruiz/Downloads/Compound/LemonPark/"

def create_pdf(image_path, height_ft, label, width_ft=2, dpi=600, double_blade=False, spacing_points=20):
    """
    Create a tiled large-format PDF from an image, then overlay the correct footer at the bottom.
    """
    try:
        # Convert feet to points (1 inch = 72 points, 1 foot = 12 inches)
        tile_width_points = width_ft * 12 * 72
        total_height_points = height_ft * 12 * 72
        
        if double_blade:
            total_width_points = 2 * tile_width_points + spacing_points
            output_pdf = f"temp_{height_ft}ft_{label}_DoubleBlade.pdf"
        else:
            total_width_points = tile_width_points
            output_pdf = f"temp_{height_ft}ft_{label}.pdf"

        # Open the image and enhance quality
        img = Image.open(image_path).convert("RGB")
        img_width, img_height = img.size
        
        # Calculate scaling factor
        scale_factor = tile_width_points / img_width
        new_width = tile_width_points
        new_height = int(img_height * scale_factor)
        
        # Resize image using high-quality resampling
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate the number of times the image should be repeated vertically
        tile_count = (total_height_points // new_height) + 1

        # Create PDF
        c = canvas.Canvas(output_pdf, pagesize=(total_width_points, total_height_points))
        c.setAuthor("Automated PDF Generator")
        c.setTitle(f"{label} {height_ft}ft {'Double Blade' if double_blade else ''}")

        y_position = 0
        for _ in range(tile_count):
            c.drawImage(image_path, 0, y_position, new_width, new_height, preserveAspectRatio=True, mask='auto')
            if double_blade:
                c.drawImage(image_path, new_width + spacing_points, y_position, new_width, new_height, preserveAspectRatio=True, mask='auto')
            y_position += new_height  # Move up for the next tile

        c.showPage()
        c.save()
        
        print(f"Temporary PDF saved to {output_pdf}")

        # Overlay footer at the bottom
        overlay_footer(output_pdf, height_ft, label)

    except Exception as e:
        print(f"Error: {e}")

def overlay_footer(base_pdf_path, height_ft, label):
    """
    Fully overlay the footer onto the generated base PDF at the exact bottom, preserving background color.
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

        # Extract footer as an image to preserve background
        footer_page = footer_pdf[0]
        footer_pixmap = footer_page.get_pixmap(alpha=False)  # Preserve colors
        footer_image_path = f"footer_{height_ft}_{label}.png"
        footer_pixmap.save(footer_image_path)

        for page_num in range(len(base_pdf)):
            base_page = base_pdf[page_num]
            base_rect = base_page.rect

            # Scale footer to fit the width of the final PDF while maintaining aspect ratio
            footer_width = base_rect.width
            footer_height = footer_pixmap.height * (footer_width / footer_pixmap.width)  # Maintain aspect ratio

            # Footer should be placed at the **very bottom** of the page
            x0, y0 = 0, base_rect.height - footer_height  # Now correctly positioned at bottom
            x1, y1 = footer_width, base_rect.height

            # Overlay the footer **as an image** to preserve background color
            base_page.insert_image(fitz.Rect(x0, y0, x1, y1), filename=footer_image_path)

        # Save the final PDF with footer applied
        final_pdf_path = base_pdf_path.replace("temp_", "")
        base_pdf.save(final_pdf_path)
        base_pdf.close()
        footer_pdf.close()

        # Cleanup temporary footer image
        os.remove(footer_image_path)

        print(f"Final PDF with footer saved as {final_pdf_path}")

        # Clean up temporary file
        os.remove(base_pdf_path)

    except Exception as e:
        print(f"Error overlaying footer: {e}")

if __name__ == "__main__":
    image_path = input("Enter the full path to the image file: ").strip()

    if not os.path.exists(image_path):
        print(f"Error: The specified image file '{image_path}' does not exist.")
    else:
        for label in ["P&S", "TRAD"]:
            for height in [13, 27]:
                create_pdf(image_path, height_ft=height, label=label)
                create_pdf(image_path, height_ft=height, label=label, double_blade=True)
