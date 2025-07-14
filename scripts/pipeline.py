#!/usr/bin/env python3
"""
Unified Resume Generation Pipeline

This script orchestrates the complete resume generation process:
1. Fetch LinkedIn profile data
2. Transform to JSON-Resume format
3. Enhance with OpenAI processing
4. Process GitHub repositories
5. Validate all URLs
6. Generate HTML resume
7. Generate PDF resume

Usage:
    python scripts/pipeline.py [--skip-linkedin] [--skip-openai] [--skip-github] [--output-dir OUTPUT_DIR]

Options:
    --skip-linkedin    Skip LinkedIn fetching step (use existing data)
    --skip-openai      Skip OpenAI processing step
    --skip-github      Skip GitHub repository processing step
    --output-dir       Custom output directory for generated files
"""

import argparse
import logging
import pathlib
import sys
import time
from typing import Optional
import os

# Import our modular functions
from linkedin_fetcher import fetch_linkedin_data
from linkedin_transformer import transform_linkedin_data
from openai_processor import enhance_resume_with_openai
from github_processor import enhance_resume_with_github_projects
from html_generator import generate_html_resume_file
from pdf_generator import generate_pdf_resume
from url_validator import validate_resume_urls
from job_searcher import search_and_save_jobs
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
    log.info(f"\n{'='*60}")
    log.info(f"STEP {step_num}/{total_steps}: {title}")
    log.info(f"{'='*60}")
    log.info(f"📝 {description}")
    log.info("")

def print_step_success(title: str, details: str = ""):
    """Print step success message."""
    log.info(f"✅ {title} completed successfully")
    if details:
        log.info(f"   {details}")

def print_step_error(title: str, error: str):
    """Print step error message."""
    log.error(f"❌ {title} failed: {error}")

def print_pipeline_summary(start_time: float, steps_completed: int, total_steps: int):
    """Print pipeline completion summary."""
    duration = time.time() - start_time
    log.info(f"\n{'='*60}")
    log.info(f"PIPELINE SUMMARY")
    log.info(f"{'='*60}")
    log.info(f"⏱️  Total time: {duration:.2f} seconds")
    log.info(f"✅ Steps completed: {steps_completed}/{total_steps}")
    
    if steps_completed == total_steps:
        log.info(f"🎉 Resume generation pipeline completed successfully!")
        log.info(f"📄 HTML saved to: {config.ASSETS_DIR}/{config.RESUME_HTML_FILE}")
        log.info(f"📄 PDF saved to: {config.ASSETS_DIR}/{config.RESUME_PDF_FILE}")
        log.info(f"💼 Job search results saved to: {config.ASSETS_DIR}/{config.JOB_SEARCH_RESULTS_FILE}")
    else:
        log.warning(f"⚠️  Pipeline incomplete. Check logs above for errors.")

def step_1_fetch_linkedin(skip: bool = False) -> bool:
    """Step 1: Fetch LinkedIn profile data."""
    if skip:
        log.info("⏭️  Skipping LinkedIn fetch (--skip-linkedin flag provided)")
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
        print_step_success("Data transformation", f"Resume data saved to {config.DATA_DIR}/{config.RESUME_JSON_FILE}")
        return True
    except SystemExit as e:
        if e.code == 1:
            log.info("ℹ️  No changes detected - resume already up-to-date")
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
        log.info("⏭️  Skipping OpenAI processing (--skip-openai flag provided)")
        return True
    
    try:
        enhanced_data = enhance_resume_with_openai()
        print_step_success("OpenAI enhancement", f"Enhanced data saved to {config.DATA_DIR}/{config.RESUME_JSON_FILE}")
        return True
    except SystemExit:
        print_step_error("OpenAI enhancement", "Processing failed")
        return False
    except Exception as e:
        print_step_error("OpenAI enhancement", str(e))
        return False

def step_4_github_processing(skip: bool = False) -> bool:
    """Step 4: Process GitHub repositories and enhance projects."""
    if skip:
        log.info("⏭️  Skipping GitHub processing (--skip-github flag provided)")
        return True
    
    try:
        from openai_processor import load_resume_data, save_enhanced_resume_data
        from github_processor import enhance_resume_with_github_projects_async
        import asyncio
        
        # Load current resume data
        resume_data = load_resume_data()
        
        # Get GitHub username from config
        github_username = config.GITHUB_USERNAME
        
        # Enhance with GitHub projects using async function
        # Use asyncio.run() to ensure we have a clean event loop
        enhanced_data = asyncio.run(enhance_resume_with_github_projects_async(resume_data, github_username))
        
        # Save back the enhanced data
        save_enhanced_resume_data(enhanced_data)
        
        print_step_success("GitHub processing", f"GitHub projects processed and integrated")
        return True
    except Exception as e:
        print_step_error("GitHub processing", str(e))
        return False

def step_5_validate_urls() -> bool:
    """Step 5: Validate all URLs in resume data."""
    try:
        from openai_processor import load_resume_data, save_enhanced_resume_data
        
        # Load current resume data
        resume_data = load_resume_data()
        
        # Validate URLs
        validated_data = validate_resume_urls(resume_data)
        
        # Save back the validated data
        save_enhanced_resume_data(validated_data)
        
        print_step_success("URL validation", "All URLs checked and invalid ones removed")
        return True
    except Exception as e:
        print_step_error("URL validation", str(e))
        return False

def step_6_generate_html() -> bool:
    """Step 6: Generate HTML resume."""
    try:
        html_path = generate_html_resume_file()
        print_step_success("HTML generation", f"HTML saved to {html_path}")
        return True
    except SystemExit:
        print_step_error("HTML generation", "Generation failed")
        return False
    except Exception as e:
        print_step_error("HTML generation", str(e))
        return False

def step_7_generate_pdf() -> bool:
    """Step 7: Generate PDF resume from HTML."""
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

def step_8_job_search(skip: bool = False) -> bool:
    """Step 8: Search for ML/AI jobs and save results."""
    if skip:
        log.info("⏭️  Skipping job search (--skip-job-search flag provided)")
        return True
    
    try:
        jobs_path = search_and_save_jobs()
        print_step_success("Job search", f"Job search results saved to {jobs_path}")
        return True
    except Exception as e:
        print_step_error("Job search", str(e))
        return False

def run_pipeline(skip_linkedin: bool = False, skip_openai: bool = False, skip_github: bool = False, skip_job_search: bool = False, output_dir: Optional[str] = None) -> bool:
    """
    Run the complete resume generation pipeline.
    
    Args:
        skip_linkedin (bool): Skip LinkedIn fetching step
        skip_openai (bool): Skip OpenAI processing step
        skip_github (bool): Skip GitHub repository processing step
        skip_job_search (bool): Skip job search step
        output_dir (str, optional): Custom output directory
        
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    start_time = time.time()
    total_steps = 8
    steps_completed = 0
    
    log.info(f"\n🚀 Starting Resume Generation Pipeline")
    log.info(f"📁 Working directory: {ROOT}")
    if output_dir:
        log.info(f"📂 Output directory: {output_dir}")
    log.info(f"⚙️  Configuration: LinkedIn={'Skip' if skip_linkedin else 'Fetch'}, OpenAI={'Skip' if skip_openai else 'Process'}, GitHub={'Skip' if skip_github else 'Process'}, JobSearch={'Skip' if skip_job_search else 'Search'}")
    
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
                     "Filter skills, categorize, and extract bullet points")
    if step_3_openai_enhancement(skip=skip_openai):
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 4: GitHub Processing
    print_step_header(4, total_steps, "GITHUB PROCESSING", 
                     "Fetch GitHub repositories and extract project information from READMEs")
    if step_4_github_processing(skip=skip_github):
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 5: Validate URLs
    print_step_header(5, total_steps, "VALIDATE URLS", 
                     "Check all URLs are accessible and remove broken ones")
    if step_5_validate_urls():
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 6: Generate HTML
    print_step_header(6, total_steps, "GENERATE HTML", 
                     "Create professional HTML resume with responsive design")
    if step_6_generate_html():
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 7: Generate PDF
    print_step_header(7, total_steps, "GENERATE PDF", 
                     "Create PDF resume from HTML using Playwright")
    if step_7_generate_pdf():
        steps_completed += 1
    else:
        print_pipeline_summary(start_time, steps_completed, total_steps)
        return False
    
    # Step 8: Job Search
    print_step_header(8, total_steps, "JOB SEARCH", 
                     "Search for ML/AI full-time positions and save results")
    if step_8_job_search(skip=skip_job_search):
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
        description="Generate HTML and PDF resume from LinkedIn profile data using OpenAI enhancement and GitHub projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pipeline.py                    # Full pipeline
  python scripts/pipeline.py --skip-linkedin   # Skip LinkedIn fetch, use existing data
  python scripts/pipeline.py --skip-openai     # Skip OpenAI processing
  python scripts/pipeline.py --skip-github     # Skip GitHub repository processing
  python scripts/pipeline.py --skip-job-search # Skip job search step
  python scripts/pipeline.py --skip-linkedin --skip-openai --skip-github --skip-job-search  # Only generate HTML and PDF from existing JSON
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
        "--skip-github",
        action="store_true", 
        help="Skip GitHub repository processing step"
    )
    
    parser.add_argument(
        "--skip-job-search",
        action="store_true", 
        help="Skip job search step"
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
        skip_github=args.skip_github,
        skip_job_search=args.skip_job_search,
        output_dir=args.output_dir
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 