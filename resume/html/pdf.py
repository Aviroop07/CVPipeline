#!/usr/bin/env python3
"""
PDF resume generation module using Playwright.

This module provides functions to generate PDF resumes from HTML files using Playwright's browser engine.
"""

import pathlib
import sys
import logging
from resume.utils import config

# Try to import Playwright for HTML-to-PDF generation
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    PLAYWRIGHT_AVAILABLE = False

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def html_to_pdf(html_path: pathlib.Path, out_path: pathlib.Path):
    """Convert HTML file to PDF using Playwright's browser engine.
    
    Args:
        html_path (pathlib.Path): Path to HTML file
        out_path (pathlib.Path): Path where PDF should be saved
        
    Raises:
        SystemExit: If Playwright is not available or PDF generation fails
    """
    if not PLAYWRIGHT_AVAILABLE:
        log.error("Playwright not available - please install with: playwright install chromium")
        sys.exit(1)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])           # headless by default
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")                            # apply @media print styles
            page.pdf(                                                   # pixel-perfect output
                path=str(out_path),
                format="A4",
                print_background=True
            )
            browser.close()
        log.info("PDF generated using Playwright at %s", out_path.relative_to(config.PROJECT_ROOT))
    except Exception as e:
        log.error(f"PDF generation failed: {e}")
        sys.exit(1)

def generate_pdf_from_html(html_path=None, output_path=None):
    """Generate PDF from HTML file using Playwright.
    
    Args:
        html_path (pathlib.Path, optional): Path to HTML file. Defaults to assets/index.html
        output_path (pathlib.Path, optional): Path for PDF output. Defaults to assets/RESUME_PDF_FILE
        
    Returns:
        pathlib.Path: Path where PDF was saved, or None if Playwright is not available
        
    Raises:
        SystemExit: If HTML file doesn't exist or PDF generation fails
    """
    if not PLAYWRIGHT_AVAILABLE:
        log.warning("Playwright not available - skipping PDF generation")
        return None
    
    if html_path is None:
        html_path = config.PROJECT_ROOT / config.ASSETS_DIR / "index.html"
    if output_path is None:
        output_path = config.PROJECT_ROOT / config.ASSETS_DIR / config.RESUME_PDF_FILE
    
    # Check if HTML file exists
    if not html_path.exists():
        log.error(f"HTML file not found: {html_path}")
        sys.exit(1)
    
    log.info("Generating PDF from HTML with Playwright...")
    html_to_pdf(html_path, output_path)
    return output_path

def generate_pdf_resume():
    """Complete PDF generation pipeline using Playwright (HTML to PDF).
    
    Returns:
        pathlib.Path: Path to generated PDF file
        
    Raises:
        SystemExit: If generation fails
    """
    # Generate PDF from HTML using Playwright
    pdf_path = generate_pdf_from_html()
    
    if pdf_path is None:
        log.error("PDF generation failed - Playwright not available")
        sys.exit(1)
    
    return pdf_path

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    generate_pdf_resume()

if __name__ == "__main__":
    main() 
