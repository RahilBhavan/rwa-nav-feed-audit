"""Download non-SEC research sources to ignored data/sources."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile, ZipFile

from issuer_history import EVIDENCE, LIMIT, USER_AGENT, read_source

DESTINATION = Path(__file__).resolve().parents[1] / "data" / "sources"


def save(path, raw):
    with NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(raw)
            handle.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def download(source, accessed, retrieve):
    name = source["download"]
    expected = source.get("original_sha256") or source["sha256"]
    report = {
        "file": name,
        "url": source["url"],
        "expected_sha256": expected,
        "expected_accessed": source.get("hash_accessed", accessed),
        "accessed": datetime.now(timezone.utc).date().isoformat(),
    }
    if "member" in source:
        report["member"] = source["member"]
    try:
        raw = retrieve(source)
        if name.endswith(".pdf") and not raw.startswith(b"%PDF-"):
            raise ValueError("expected PDF bytes")
        actual = hashlib.sha256(raw).hexdigest()
        save(DESTINATION / name, raw)
        report.update(sha256=actual, status="match" if actual == expected else "changed")
    except (OSError, HTTPException, ValueError, KeyError, BadZipFile) as exc:
        report.update(status="error", error=str(exc))
    return report


def read_archive_member(archive, source):
    with archive.open(source["member"]) as handle:
        raw = handle.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("archive member exceeds the 2 MB limit")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usdy-archive", type=Path, help="local Ondo USDY LLC daily reports ZIP")
    args = parser.parse_args()

    manifest = json.loads((EVIDENCE / "manifest.json").read_bytes())
    series = [
        source
        for product in manifest["products"].values()
        for source in product.get("series", [])
        if "download" in source
    ]
    DESTINATION.mkdir(parents=True, exist_ok=True)
    results = [
        download(source, manifest["accessed"], lambda item: read_source(item["url"], USER_AGENT))
        for source in series + manifest["supplemental_downloads"]
    ]
    if args.usdy_archive:
        specification = manifest["usdy_archive"]
        try:
            with ZipFile(args.usdy_archive) as archive:
                for member in specification["members"]:
                    source = dict(member, url=specification["url"], hash_accessed=specification["hash_accessed"])
                    results.append(download(source, manifest["accessed"],
                                            lambda item: read_archive_member(archive, item)))
        except (OSError, BadZipFile):
            results.append({"source": "USDY daily reports ZIP", "status": "error",
                            "error": "could not open archive"})
    output = json.dumps(results, indent=2)
    save(DESTINATION / "receipts.json", (output + "\n").encode())
    print(output)
    return int(any(result["status"] == "error" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
