import sys
import argparse
from resume.linkedin.fetcher import fetch_linkedin_data
from resume.linkedin.transformer import transform_linkedin_data
from resume.openai.processor import enhance_resume_with_openai
from resume.github.processor import enhance_resume_with_github_projects
from resume.html.generator import generate_html_resume_file
from resume.html.pdf import generate_pdf_resume
from resume.utils.url_validator import validate_resume_urls
from resume.jobs.searcher import search_and_save_jobs
from resume.utils import config


def main():
    parser = argparse.ArgumentParser(description="Unified Resume Generation Pipeline")
    parser.add_argument('--skip-linkedin', action='store_true', help='Skip LinkedIn fetch step')
    parser.add_argument('--skip-openai', action='store_true', help='Skip OpenAI enhancement step')
    parser.add_argument('--skip-github', action='store_true', help='Skip GitHub enhancement step')
    parser.add_argument('--skip-job-search', action='store_true', help='Skip job search step')
    parser.add_argument('--cache-stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--clean-dirty-cache', action='store_true', help='Clean expired cache entries')
    parser.add_argument('--clear-cache', action='store_true', help='Clear all cache before running')
    args = parser.parse_args()

    # Example: cache management logic (implement as needed)
    if args.cache_stats:
        print("[Cache] Show cache statistics (implement in resume.utils.api_cache)")
        sys.exit(0)
    if args.clean_dirty_cache:
        print("[Cache] Clean expired cache entries (implement in resume.utils.api_cache)")
        sys.exit(0)
    if args.clear_cache:
        print("[Cache] Clear all cache before running (implement in resume.utils.api_cache)")
        sys.exit(0)

    # Pipeline steps
    if not args.skip_linkedin:
        fetch_linkedin_data()
    transform_linkedin_data()
    if not args.skip_openai:
        enhance_resume_with_openai()
    if not args.skip_github:
        enhance_resume_with_github_projects()
    validate_resume_urls()
    generate_html_resume_file()
    generate_pdf_resume()
    if not args.skip_job_search:
        search_and_save_jobs()

if __name__ == "__main__":
    main() 