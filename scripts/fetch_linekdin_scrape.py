from linkedin_api import Linkedin
import json, os, pathlib, sys, dotenv

OUT = pathlib.Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)
DST = OUT / "linkedin_raw.json"

dotenv.load_dotenv()

def main() -> None:
    # ── 1. Read creds from env ─────────────────────────
    try:
        user = os.environ["LI_USER"]
        pwd  = os.environ["LI_PASS"]
        public_id = os.environ["LI_PID"]
        # print(f"User: {user}, Password: {pwd}")
    except KeyError as miss:
        sys.exit(f"Env var {miss} missing")

    # ── 2. Login the way the library expects ───────────
    api = Linkedin(user, pwd, refresh_cookies=False)

    profile = api.get_profile(public_id=public_id)                         # ← no contact_info arg
    contact = api.get_profile_contact_info(
        public_id=profile.get("public_id")
    )
    profile["contact_info"] = contact                  # merge if you want it
    # print(profile)
    # 4 ─ write to disk
    DST.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"✅ wrote {DST.relative_to(OUT)}")

if __name__ == "__main__":
    main()
