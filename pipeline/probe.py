#!/usr/bin/env python3
"""Stage 1: probe candidate assets and record what is actually retrievable.

Records only observed facts: HTTP status, final URL after redirects, media type,
byte size, SHA-256, TLS validity, and whether an RDF Accept header yields RDF.
Nothing here interprets or scores. Interpretation happens in assess.py.
"""
import hashlib
import json
import pathlib
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "SemanticAssetRegister/0.1 (+https://gov.tesseract.academy/def/sar; research audit; contact fabio@thetesseractacademy.com)"
RDF_ACCEPT = "text/turtle;q=1.0, application/rdf+xml;q=0.9, application/n-triples;q=0.8, application/ld+json;q=0.7, */*;q=0.1"
TIMEOUT = 60
MAX_BYTES = 400 * 1024 * 1024


def fetch(url, accept, timeout=TIMEOUT):
    """Return an observation dict. Never raises; failures are data."""
    obs = {
        "requested_url": url,
        "accept": accept,
        "http_status": None,
        "final_url": None,
        "media_type": None,
        "byte_size": None,
        "sha256": None,
        "tls_ok": None,
        "error": None,
        "elapsed_s": None,
    }
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(MAX_BYTES)
            obs["http_status"] = resp.status
            obs["final_url"] = resp.geturl()
            obs["media_type"] = resp.headers.get("Content-Type")
            obs["byte_size"] = len(body)
            obs["sha256"] = hashlib.sha256(body).hexdigest()
            obs["tls_ok"] = obs["final_url"].startswith("https://") or None
            obs["_body"] = body
    except urllib.error.HTTPError as e:
        obs["http_status"] = e.code
        obs["final_url"] = e.url
        obs["media_type"] = e.headers.get("Content-Type") if e.headers else None
        obs["error"] = f"HTTPError {e.code} {e.reason}"
    except ssl.SSLError as e:
        obs["tls_ok"] = False
        obs["error"] = f"SSLError {e}"
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLCertVerificationError):
            obs["tls_ok"] = False
            obs["error"] = f"SSLCertVerificationError {e.reason}"
        else:
            obs["error"] = f"URLError {e.reason}"
    except Exception as e:  # noqa: BLE001 - failures are data, not crashes
        obs["error"] = f"{type(e).__name__}: {e}"
    obs["elapsed_s"] = round(time.time() - t0, 2)
    return obs


def main():
    seed = json.loads((ROOT / "data" / "seed_assets.json").read_text())
    outdir = ROOT / "data" / "snapshots"
    outdir.mkdir(parents=True, exist_ok=True)
    results = []

    for a in seed["assets"]:
        print(f"[probe] {a['id']:26s} {a['url']}", flush=True)
        rec = {
            "id": a["id"],
            "agency": a["agency"],
            "name": a["name"],
            "namespace": a["namespace"],
            "kind_hint": a.get("kind_hint"),
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

        # 1. the advertised download URL, asking for RDF
        main_obs = fetch(a["url"], RDF_ACCEPT)
        body = main_obs.pop("_body", None)
        rec["download"] = main_obs
        if body:
            path = outdir / f"{a['id']}.bin"
            path.write_bytes(body)
            rec["snapshot_path"] = str(path.relative_to(ROOT))

        # 2. the namespace URI itself, asking for RDF (SAR-R02, SAR-R03)
        ns = a.get("namespace")
        if ns:
            ns_obs = fetch(ns, RDF_ACCEPT, timeout=45)
            ns_obs.pop("_body", None)
            rec["namespace_rdf"] = ns_obs
            html_obs = fetch(ns, "text/html", timeout=45)
            html_obs.pop("_body", None)
            rec["namespace_html"] = html_obs

        # 3. HTTP variant, to test whether HTTPS is enforced (SAR-R04)
        if a["url"].startswith("https://"):
            http_url = "http://" + a["url"][len("https://"):]
            http_obs = fetch(http_url, RDF_ACCEPT, timeout=30)
            http_obs.pop("_body", None)
            rec["http_variant"] = http_obs

        results.append(rec)
        time.sleep(1.0)  # be a polite citizen against government infrastructure

    out = ROOT / "results" / "probe_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"\n[probe] wrote {out} ({len(results)} assets)")

    ok = sum(1 for r in results if r["download"].get("http_status") == 200)
    print(f"[probe] download URL returned 200 for {ok}/{len(results)} assets")


if __name__ == "__main__":
    sys.exit(main())
