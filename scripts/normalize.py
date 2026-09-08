"""Website/company normalization for lead dedupe.

The Pipeline sheet dedupes on a normalized website (column C). Getting this wrong means
double-emailing a prospect, so it has a self-check. Run:  python scripts/normalize.py
"""
import re
import sys

_SCHEME = re.compile(r"^[a-z]+://", re.I)
_PORT = re.compile(r":\d+$")


def normalize_domain(value: str) -> str:
    """Reduce any URL / domain / email-ish string to a bare registrable host.

    'https://www.Acme.co.uk/contact?x=1' -> 'acme.co.uk'
    'Acme Corp' (no dot) -> '' (not a domain; caller falls back to company-name match)
    """
    if not value:
        return ""
    v = value.strip().lower()
    if "@" in v and "/" not in v:  # bare email -> take the domain
        v = v.split("@", 1)[1]
    v = _SCHEME.sub("", v)
    v = v.split("/", 1)[0]          # drop path
    v = v.split("?", 1)[0].split("#", 1)[0]
    v = _PORT.sub("", v)
    if v.startswith("www."):
        v = v[4:]
    v = v.strip(".")
    return v if "." in v else ""


def same_lead(a_site: str, b_site: str, a_name: str = "", b_name: str = "") -> bool:
    """True if two rows are the same company."""
    da, db = normalize_domain(a_site), normalize_domain(b_site)
    if da and db:
        return da == db
    na, nb = _name_key(a_name), _name_key(b_name)
    return bool(na) and na == nb


def _name_key(name: str) -> str:
    n = (name or "").strip().lower()
    n = re.sub(r"[^a-z0-9 ]", "", n)
    n = re.sub(r"\b(inc|llc|ltd|limited|corp|co|company|group|holdings|gmbh)\b", "", n)
    return re.sub(r"\s+", " ", n).strip()


def demo() -> None:
    assert normalize_domain("https://www.Acme.co.uk/contact?x=1") == "acme.co.uk"
    assert normalize_domain("HTTP://Acme.com") == "acme.com"
    assert normalize_domain("acme.com/") == "acme.com"
    assert normalize_domain("www.acme.com:8080") == "acme.com"
    assert normalize_domain("jane@acme.com") == "acme.com"
    assert normalize_domain("Acme Corporation") == ""
    assert normalize_domain("") == ""
    assert same_lead("https://acme.com", "http://www.acme.com/about")
    assert same_lead("", "", "Acme, Inc.", "acme llc")
    assert not same_lead("acme.com", "acme-corp.com")
    assert not same_lead("", "", "Acme", "Globex")
    print("normalize.py: all checks passed")


if __name__ == "__main__":
    demo() if len(sys.argv) == 1 else print(normalize_domain(sys.argv[1]))
