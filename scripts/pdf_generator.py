#!/usr/bin/env python3
"""
PDF resume generation module using WeasyPrint.

This module provides functions to generate PDF resumes from HTML files using WeasyPrint.
"""

import pathlib
import sys
import logging
import config

# Try to import WeasyPrint for HTML-to-PDF generation
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def generate_pdf_from_html(html_path=None, css_path=None, output_path=None):
    """Generate PDF from HTML file using WeasyPrint.
    
    Args:
        html_path (pathlib.Path, optional): Path to HTML file. Defaults to assets/index.html
        css_path (pathlib.Path, optional): Path to CSS file. Defaults to assets/styles.css
        output_path (pathlib.Path, optional): Path for PDF output. Defaults to assets/RESUME_PDF_FILE
        
    Returns:
        pathlib.Path: Path where PDF was saved, or None if WeasyPrint is not available
        
    Raises:
        SystemExit: If HTML file doesn't exist or PDF generation fails
    """
    if not WEASYPRINT_AVAILABLE:
        log.warning("WeasyPrint not available - skipping PDF generation")
        return None
    
    if html_path is None:
        html_path = ROOT / config.ASSETS_DIR / "index.html"
    if css_path is None:
        css_path = ROOT / config.ASSETS_DIR / "styles.css"
    if output_path is None:
        output_path = ROOT / config.ASSETS_DIR / config.RESUME_PDF_FILE
    
    # Check if HTML file exists
    if not html_path.exists():
        log.error(f"HTML file not found: {html_path}")
        sys.exit(1)
    
    try:
        # Generate PDF using WeasyPrint
        log.info("Generating PDF from HTML with WeasyPrint...")
        html = HTML(filename=str(html_path), encoding="utf-8")
        
        # Create CSS to override WeasyPrint's default margins completely
        pdf_reset_css = CSS(string='''
            @page { size: A4; margin: 0; }
            html { margin: 0 !important; padding: 0 !important; }
        ''')
        
        # Combine PDF reset CSS with existing styles
        stylesheets = [pdf_reset_css]
        if css_path.exists():
            stylesheets.append(str(css_path))
        
        html.write_pdf(
            target=str(output_path),
            stylesheets=stylesheets,
            pdf_forms=False
        )
        
        log.info("PDF generated → %s", output_path.relative_to(ROOT))
        return output_path
        
    except Exception as e:
        log.error(f"PDF generation failed: {e}")
        sys.exit(1)

def generate_pdf_resume():
    """Complete PDF generation pipeline using WeasyPrint (HTML to PDF).
    
    Returns:
        pathlib.Path: Path to generated PDF file
        
    Raises:
        SystemExit: If generation fails
    """
    # Generate PDF from HTML using WeasyPrint
    pdf_path = generate_pdf_from_html()
    
    if pdf_path is None:
        log.error("PDF generation failed - WeasyPrint not available")
        sys.exit(1)
    
    return pdf_path

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    generate_pdf_resume()

if __name__ == "__main__":
    main() 