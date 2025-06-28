#!/usr/bin/env python3
import json, os, pathlib, sys, dotenv
dotenv.load_dotenv()
from linkedin_api import Linkedin
from requests.cookies import RequestsCookieJar

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT  = ROOT / "data";      OUT.mkdir(exist_ok=True)
DST  = OUT  / "linkedin_raw.json"
        

def main():
    try:
        user  = os.environ["LI_USER"]
        pwd   = os.environ["LI_PASS"]
        seed  = os.environ["LI_TOTP_SECRET"]
        # Debug: print environment variables in use
        print("🔧 Environment variables:")
        for var in (
            "LI_USER",
            "LI_PASS",
            "LI_TOTP_SECRET",
            "LI_AT",
            "LI_JSESSIONID",
            "LI_PID",
        ):
            print(f"  {var} = {os.getenv(var)}")
    except KeyError as miss:
        sys.exit(f"✖ missing env var {miss}")

    try:
        print("🔐 Authenticating with LinkedIn via cookies...")

        li_at       = os.getenv("LI_AT", "").strip()
        jsessionid  = os.getenv("LI_JSESSIONID", "").strip()

        if li_at and jsessionid:
            # Build a cookie jar with existing session cookies
            jar = RequestsCookieJar()
            jar.set("li_at", li_at, domain=".linkedin.com", path="/")
            jar.set("JSESSIONID", jsessionid, domain=".linkedin.com", path="/")

            # Initialize LinkedIn API with cookie jar (username/password are unused in this case)
            api = Linkedin("", "", cookies=jar)
            print("✅ Authenticated via cookies")
        else:
            # Fallback to username/password auth (may trigger 2FA challenge)
            print("🔐 Cookies not provided – falling back to username/password auth. This may be less reliable on GitHub Actions.")
            api = Linkedin(user, pwd)
            print("✅ Authenticated via credentials")
        
        print("📄 Fetching profile...")
        profile = api.get_profile(public_id=os.environ["LI_PID"])
        print("✅ Profile fetched successfully")
        
        print("📞 Fetching contact info...")
        profile["contact_info"] = api.get_profile_contact_info(
            public_id=profile["public_id"]
        )
        print("✅ Contact info fetched successfully")

        DST.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"✅ wrote {DST.relative_to(ROOT)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
