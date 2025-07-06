#!/usr/bin/env python3
"""
Unified Resume Generation Pipeline

This script orchestrates the complete resume generation process:
1. Fetch LinkedIn profile data
2. Transform to JSON-Resume format
3. Enhance with OpenAI processing
4. Generate PDF resume

Usage:
    python scripts/pipeline.py [--skip-linkedin] [--skip-openai] [--output-dir OUTPUT_DIR]

Options:
    --skip-linkedin    Skip LinkedIn fetching step (use existing data)
    --skip-openai      Skip OpenAI processing step
    --output-dir       Custom output directory for generated files
"""

import argparse
import logging
import pathlib
import sys
import time
from typing import Optional

# Import our modular functions
from linkedin_fetcher import fetch_linkedin_data
from linkedin_transformer import transform_linkedin_data
from openai_processor import enhance_resume_with_openai
from pdf_generator import generate_pdf_resume
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parent.parent

def print_step_header(step_num: int, total_steps: int, title: str, description: str):
    """Print a formatted step header."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}/{total_steps}: {title}")
    print(f"{'='*60}")
    print(f"📝 {description}")
    print()

def print_step_success(title: str, details: str = ""):
    """Print step success message."""
    print(f"✅ {title} completed successfully")
    if details:
        print(f"   {details}")

def print_step_error(title: str, error: str):
    """Print step error message."""
    print(f"❌ {title} failed: {error}")

def print_pipeline_summary(start_time: float, steps_completed: int, total_steps: int):
    """Print pipeline completion summary."""
    duration = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"⏱️  Total time: {duration:.2f} seconds")
    print(f"✅ Steps completed: {steps_completed}/{total_steps}")
    
    if steps_completed == total_steps:
        print(f"🎉 Resume generation pipeline completed successfully!")
        print(f"📄 PDF saved to: {config.RESUME_PDF_FILE}")
    else:
        print(f"⚠️  Pipeline incomplete. Check logs above for errors.")

def step_1_fetch_linkedin(skip: bool = False) -> bool:
    """Step 1: Fetch LinkedIn profile data."""
    if skip:
        print("⏭️  Skipping LinkedIn fetch (--skip-linkedin flag provided)")
        return True
    
    try:
        profile_data = fetch_linkedin_data()
        print_step_success("LinkedIn data fetched", f"Profile data saved to {config.DATA_DIR}/{config.LINKEDIN_RAW_FILE}")
        return True
    except SystemExit:
        # fetch_linkedin_data uses sys.exit on error
        print_step_error("LinkedIn fetch", "Authentication or API error")
        return False
    except Exception as e:
        print_step_error("LinkedIn fetch", str(e))
        return False

def step_2_transform_data() -> bool:
    """Step 2: Transform LinkedIn data to JSON-Resume format."""
    try:
        resume_data = transform_linkedin_data()
        print_step_success("Data transformation", f"Resume data saved to {config.RESUME_JSON_FILE}")
        return True
    except SystemExit as e:
        if e.code == 1:
            print("ℹ️  No changes detected - resume already up-to-date")
            return True  # This is actually success for our pipeline
        else:
            print_step_error("Data transformation", "Transformation failed")
            return False
    except Exception as e:
        print_step_error("Data transformation", str(e))
        return False

def step_3_openai_enhancement(skip: bool = False) -> bool:
    """Step 3: Enhance resume data with OpenAI processing."""
    if skip:
        print("⏭️  Skipping OpenAI processing (--skip-openai flag provided)")
        return True
    
    try:
        enhanced_data = enhance_resume_with_openai()
        print_step_success("OpenAI enhancement", f"Enhanced data saved to {config.RESUME_JSON_FILE}")
        return True
    except SystemExit:
        print_step_error("OpenAI enhancement", "Processing failed")
        return False
    except Exception as e:
        print_step_error("OpenAI enhancement", str(e))
        return False

def step_4_generate_pdf() -> bool:
    """Step 4: Generate PDF resume."""
    try:
        pdf_path = generate_pdf_resume()
        print_step_success("PDF generation", f"PDF saved to {pdf_path}")
        return True
    except SystemExit:
        print_step_error("PDF generation", "Generation failed")
        return False
    except Exception as e:
        print_step_error("PDF generation", str(e))
        return False

def run_pipeline(skip_linkedin: bool = False, skip_openai: bool = False, output_dir: Optional[str] = None) -> bool:
    """
    Run the complete resume generation pipeline.
    
    Args:
        skip_linkedin (bool): Skip LinkedIn fetching step
        skip_openai (bool): Skip OpenAI processing step
        output_dir (str, optional): Custom output directory
        
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    start_time = time.time()
    total_steps = 4
    steps_completed = 0
    
    print(f"\n🚀 Starting Resume Generation Pipeline")
    print(f"📁 Working directory: {ROOT}")
    if output_dir:
        print(f"📂 Output directory: {output_dir}")
    print(f"⚙️  Configuration: LinkedIn={'Skip' if skip_linkedin else 'Fetch'}, OpenAI={'Skip' if skip_openai else 'Process'}")
    
    # Step 1: Fetch LinkedIn Data
    print_step_header(1, total_steps, "FETCH LINKEDIN DATA", 
                     "Authenticate with LinkedIn and fetch profile information")
    if step_1_fetch_linkedin(skip=skip_linkedin):
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 2: Transform Data
    print_step_header(2, total_steps, "TRANSFORM DATA", 
                     "Convert LinkedIn profile data to JSON-Resume format")
    if step_2_transform_data():
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 3: OpenAI Enhancement
    print_step_header(3, total_steps, "OPENAI ENHANCEMENT", 
                     "Filter skills, categorize, rank sections, and extract bullet points")
    if step_3_openai_enhancement(skip=skip_openai):
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 4: Generate PDF
    print_step_header(4, total_steps, "GENERATE PDF", 
                     "Create professional PDF resume using borb library")
    if step_4_generate_pdf():
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Pipeline completed successfully
    print_pipeline_summary(start_time, steps_completed, total_steps)
    return True

def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate resume from LinkedIn profile data using OpenAI enhancement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pipeline.py                    # Full pipeline
  python scripts/pipeline.py --skip-linkedin   # Skip LinkedIn fetch, use existing data
  python scripts/pipeline.py --skip-openai     # Skip OpenAI processing
  python scripts/pipeline.py --skip-linkedin --skip-openai  # Only generate PDF from existing JSON
        """
    )
    
    parser.add_argument(
        "--skip-linkedin",
        action="store_true",
        help="Skip LinkedIn fetching step and use existing data"
    )
    
    parser.add_argument(
        "--skip-openai", 
        action="store_true",
        help="Skip OpenAI processing step"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for generated files"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run pipeline
    success = run_pipeline(
        skip_linkedin=args.skip_linkedin,
        skip_openai=args.skip_openai,
        output_dir=args.output_dir
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 