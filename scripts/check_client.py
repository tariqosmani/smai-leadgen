"""Active-client config check.

Resolves the active client (a `client=<slug>` / bare slug argument, else
`ACTIVE_CLIENT` in `.env`, else the same in `.env.example`) and asserts that
`clients/<slug>/` has every required file and each file carries its required
sections. Getting this wrong means a skill runs with a half-configured client.

If the client's `crm_target` is not `airtable`, also assert that the pipeline
adapter doc exists and the `.env` var(s) named in `identity.md` are set.

Run:  python scripts/check_client.py
      python scripts/check_client.py acme
      python scripts/check_client.py client=acme
      python scripts/check_client.py --selftest
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENTS = ROOT / "clients"

# file -> substrings that must all appear (case-insensitive)
REQUIRED = {
    "identity.md": ["business name", "founder", "from-name", "from-email", "reply-to", "crm_target"],
    "icp.md":      ["industr", "exclusi", "intent signal"],
    "scoring.md":  ["rubric", "banding"],
    "voice.md":    ["voice"],
    "offer.md":    ["service line", "portfolio", "pricing"],
}


def resolve_client(argv):
    for a in argv[1:]:
        a = a.strip()
        if a.startswith("client="):
            a = a.split("=", 1)[1].strip()
        if a:
            return a, "argument"
    for fname in (".env", ".env.example"):
        f = ROOT / fname
        if not f.exists():
            continue
        for raw in f.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            if key.strip() == "ACTIVE_CLIENT":
                val = val.split("#", 1)[0].strip().strip('"').strip("'")
                if val:
                    return val, fname
    return None, None


def check(slug):
    d = CLIENTS / slug
    if not d.is_dir():
        return [f"clients/{slug}/ does not exist"]
    problems = []
    for fname, needles in REQUIRED.items():
        f = d / fname
        if not f.is_file():
            problems.append(f"missing clients/{slug}/{fname}")
            continue
        text = f.read_text(encoding="utf-8").lower()
        if not text.strip():
            problems.append(f"empty clients/{slug}/{fname}")
            continue
        for n in needles:
            if n.lower() not in text:
                problems.append(f"clients/{slug}/{fname}: no '{n}' section")
    return problems


# --- CRM target wiring check (only bites when crm_target != airtable) ---

def _identity_value(text, key):
    """Value after a `- **key:** value` / `key: value` line in a client md file."""
    m = re.search(rf"^[\s\-*>]*{re.escape(key)}[\s*:]+`?([^\s`]+)", text, re.I | re.M)
    return m.group(1).lower() if m else None


def _crm_env_vars(text):
    """The UPPER_SNAKE names on any line that mentions a `crm_*_env` key."""
    names = []
    for line in text.splitlines():
        if re.search(r"crm_\w*_env", line, re.I):
            names += re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", line)
    return names


def _env_is_set(name):
    if os.environ.get(name, "").strip():
        return True
    f = ROOT / ".env"
    if f.is_file():
        for raw in f.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == name and v.split("#", 1)[0].strip().strip('"').strip("'"):
                return True
    return False


def check_crm(slug):
    identity = CLIENTS / slug / "identity.md"
    if not identity.is_file():
        return []  # already reported by check()
    text = identity.read_text(encoding="utf-8")
    target = _identity_value(text, "crm_target") or "airtable"
    if target == "airtable":
        return []  # Airtable token lives in .mcp.json, nothing to assert here
    problems = []
    if not (ROOT / "docs" / "pipeline-adapters" / f"{target}.md").is_file():
        problems.append(f"crm_target '{target}': docs/pipeline-adapters/{target}.md is missing")
    env_vars = _crm_env_vars(text)
    if not env_vars:
        problems.append(
            f"crm_target '{target}': identity.md must name the .env var(s) to read, "
            f"e.g. 'crm_api_key_env: {target.upper()}_API_KEY'"
        )
    for name in env_vars:
        if not _env_is_set(name):
            problems.append(
                f"crm_target '{target}': env var {name} (named in identity.md) is not set in .env or the environment"
            )
    return problems


def _selftest():
    t = "- **crm_target:** instantly\n- **crm_api_key_env:** INSTANTLY_API_KEY\n"
    assert _identity_value(t, "crm_target") == "instantly", _identity_value(t, "crm_target")
    assert _crm_env_vars(t) == ["INSTANTLY_API_KEY"], _crm_env_vars(t)
    assert check_crm("smart-ai-workspace") == [], "airtable client should raise no CRM problems"
    d = CLIENTS / "_selftest_tmp"
    d.mkdir(exist_ok=True)
    try:
        (d / "identity.md").write_text(
            "- **crm_target:** instantly\n- **crm_api_key_env:** DEFINITELY_NOT_SET_XYZ\n",
            encoding="utf-8",
        )
        probs = check_crm("_selftest_tmp")
        assert any("DEFINITELY_NOT_SET_XYZ" in p for p in probs), probs
    finally:
        (d / "identity.md").unlink()
        d.rmdir()
    print("check_client.py: selftest passed")


def main():
    if "--selftest" in sys.argv[1:]:
        _selftest()
        return
    slug, src = resolve_client(sys.argv)
    if not slug:
        print("check_client.py: no active client. Set ACTIVE_CLIENT in .env or pass a slug.")
        sys.exit(1)
    print(f"check_client.py: active client '{slug}' (from {src})")
    problems = check(slug) + check_crm(slug)
    if problems:
        print("check_client.py: FAIL")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print(f"check_client.py: clients/{slug}/ OK - identity, icp, scoring, voice, offer all present with required sections")


if __name__ == "__main__":
    main()
