#!/usr/bin/env python3
"""Search and download rights-described media using only the Python standard library."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


USER_AGENT = "KnowledgeVideoStudio/1.0 (rights-ledger enabled)"
MAX_DOWNLOAD_BYTES = 750 * 1024 * 1024
REMOTE_PROVIDERS = {"pexels", "pixabay", "wikimedia"}
ALLOWED_HOSTS = {
    "pexels": {"videos.pexels.com", "images.pexels.com"},
    "pixabay": {"cdn.pixabay.com", "pixabay.com"},
    "wikimedia": {"upload.wikimedia.org", "commons.wikimedia.org"},
}
REQUIRED_LEDGER_FIELDS = {
    "id",
    "provider",
    "provider_asset_id",
    "creator",
    "source_page",
    "license",
    "license_url",
    "retrieved_at",
    "file_path",
    "sha256",
    "segment_ids",
    "attribution",
    "rights_notes",
}


class MediaError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_html(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _request_json(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> dict[str, Any]:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    request_headers.update(headers or {})
    req = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise MediaError(f"HTTP {exc.code} from {urllib.parse.urlsplit(url).netloc}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise MediaError(f"Request failed for {urllib.parse.urlsplit(url).netloc}: {exc}") from exc


def _query_url(base: str, params: dict[str, Any]) -> str:
    return f"{base}?{urllib.parse.urlencode(params, doseq=True)}"


def _orientation(width: int | float | None, height: int | float | None) -> str:
    width = float(width or 0)
    height = float(height or 0)
    if not width or not height:
        return "unknown"
    if abs(width - height) / max(width, height) < 0.05:
        return "square"
    return "landscape" if width > height else "portrait"


def _best_pexels_file(files: Iterable[dict[str, Any]], orientation: str) -> dict[str, Any] | None:
    candidates = [item for item in files if item.get("link") and item.get("file_type", "").startswith("video/")]
    if not candidates:
        return None

    def score(item: dict[str, Any]) -> tuple[int, int, int]:
        width = int(item.get("width") or 0)
        height = int(item.get("height") or 0)
        orient_match = int(orientation in {"any", "unknown", _orientation(width, height)})
        enough = int(max(width, height) >= 1920 or min(width, height) >= 1080)
        pixels = width * height
        return orient_match, enough, -abs(pixels - 1920 * 1080)

    return max(candidates, key=score)


def search_pexels(query: str, orientation: str, per_page: int) -> list[dict[str, Any]]:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        raise MediaError("PEXELS_API_KEY is not configured")
    params: dict[str, Any] = {"query": query, "per_page": max(1, min(per_page, 80))}
    if orientation in {"landscape", "portrait", "square"}:
        params["orientation"] = orientation
    payload = _request_json(
        _query_url("https://api.pexels.com/v1/videos/search", params),
        headers={"Authorization": key},
    )
    results: list[dict[str, Any]] = []
    for video in payload.get("videos", []):
        chosen = _best_pexels_file(video.get("video_files", []), orientation)
        if not chosen:
            continue
        creator = (video.get("user") or {}).get("name") or "Unknown Pexels creator"
        results.append(
            {
                "provider": "pexels",
                "provider_asset_id": str(video.get("id")),
                "query": query,
                "media_type": "video",
                "width": chosen.get("width"),
                "height": chosen.get("height"),
                "orientation": _orientation(chosen.get("width"), chosen.get("height")),
                "duration": video.get("duration"),
                "creator": creator,
                "source_page": video.get("url"),
                "preview_url": video.get("image"),
                "download_url": chosen.get("link"),
                "license": "Pexels License",
                "license_url": "https://www.pexels.com/license/",
                "attribution": f"Video by {creator} on Pexels",
                "rights_notes": "Pexels content license; review recognizable people, trademarks, artwork, and sensitive-context use.",
                "manual_review_required": False,
            }
        )
    return results


def _best_pixabay_file(videos: dict[str, Any], orientation: str) -> dict[str, Any] | None:
    candidates = []
    for label, item in videos.items():
        if isinstance(item, dict) and item.get("url"):
            candidate = dict(item)
            candidate["quality"] = label
            candidates.append(candidate)
    if not candidates:
        return None

    def score(item: dict[str, Any]) -> tuple[int, int, int]:
        width = int(item.get("width") or 0)
        height = int(item.get("height") or 0)
        orient_match = int(orientation in {"any", "unknown", _orientation(width, height)})
        enough = int(max(width, height) >= 1920 or min(width, height) >= 1080)
        return orient_match, enough, width * height

    return max(candidates, key=score)


def search_pixabay(query: str, orientation: str, per_page: int) -> list[dict[str, Any]]:
    key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not key:
        raise MediaError("PIXABAY_API_KEY is not configured")
    payload = _request_json(
        _query_url(
            "https://pixabay.com/api/videos/",
            {"key": key, "q": query, "per_page": max(3, min(per_page, 200)), "safesearch": "true"},
        )
    )
    results: list[dict[str, Any]] = []
    for hit in payload.get("hits", []):
        chosen = _best_pixabay_file(hit.get("videos") or {}, orientation)
        if not chosen:
            continue
        width = chosen.get("width")
        height = chosen.get("height")
        if orientation not in {"any", "unknown", _orientation(width, height)}:
            continue
        creator = hit.get("user") or "Unknown Pixabay contributor"
        results.append(
            {
                "provider": "pixabay",
                "provider_asset_id": str(hit.get("id")),
                "query": query,
                "media_type": "video",
                "width": width,
                "height": height,
                "orientation": _orientation(width, height),
                "duration": hit.get("duration"),
                "creator": creator,
                "source_page": hit.get("pageURL"),
                "preview_url": hit.get("picture_id"),
                "download_url": chosen.get("url"),
                "license": "Pixabay Content License",
                "license_url": "https://pixabay.com/service/license-summary/",
                "attribution": f"Video by {creator} on Pixabay",
                "rights_notes": "Pixabay content license; review recognizable people, trademarks, artwork, and sensitive-context use.",
                "manual_review_required": False,
            }
        )
    return results


def _commons_license_allowed(name: str) -> bool:
    normalized = re.sub(r"\s+", " ", name.lower().replace("_", "-")).strip()
    if any(token in normalized for token in ("noncommercial", "no derivatives", "-nc", "-nd")):
        return False
    return any(
        token in normalized
        for token in ("public domain", "cc0", "cc by", "cc-by", "pd-", "public-domain")
    )


def search_wikimedia(query: str, media_type: str, per_page: int) -> list[dict[str, Any]]:
    payload = _request_json(
        _query_url(
            "https://commons.wikimedia.org/w/api.php",
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 6,
                "gsrlimit": max(1, min(per_page, 50)),
                "prop": "imageinfo|info",
                "inprop": "url",
                "iiprop": "url|mime|size|extmetadata",
                "iiurlwidth": 1280,
            },
        )
    )
    results: list[dict[str, Any]] = []
    for page in (payload.get("query") or {}).get("pages", []):
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = str(info.get("mime") or "")
        actual_type = "video" if mime.startswith("video/") else "image" if mime.startswith("image/") else "other"
        if media_type != "any" and actual_type != media_type:
            continue
        meta = info.get("extmetadata") or {}
        value = lambda key: _clean_html((meta.get(key) or {}).get("value"))
        license_name = value("LicenseShortName") or value("UsageTerms") or "Unknown"
        allowed = _commons_license_allowed(license_name)
        if not allowed:
            continue
        creator = value("Artist") or value("Credit") or "Unknown Wikimedia Commons contributor"
        source_page = page.get("canonicalurl") or page.get("fullurl")
        license_url = value("LicenseUrl") or "https://commons.wikimedia.org/wiki/Commons:Licensing"
        if license_url.startswith("http://"):
            license_url = "https://" + license_url[len("http://"):]
        results.append(
            {
                "provider": "wikimedia",
                "provider_asset_id": str(page.get("pageid")),
                "query": query,
                "title": page.get("title"),
                "media_type": actual_type,
                "mime": mime,
                "width": info.get("width"),
                "height": info.get("height"),
                "orientation": _orientation(info.get("width"), info.get("height")),
                "duration": None,
                "creator": creator,
                "source_page": source_page,
                "preview_url": info.get("thumburl") or info.get("url"),
                "download_url": info.get("url"),
                "license": license_name,
                "license_url": license_url,
                "attribution": value("Attribution") or f"{page.get('title')} — {creator} — {license_name}",
                "rights_notes": "Wikimedia machine-readable metadata; confirm attribution and any share-alike obligations before publication.",
                "manual_review_required": "sa" in license_name.lower(),
            }
        )
    return results


def search_media(
    queries: list[str],
    provider: str = "auto",
    orientation: str = "landscape",
    media_type: str = "video",
    per_page: int = 8,
) -> dict[str, Any]:
    queries = [re.sub(r"\s+", " ", str(query)).strip() for query in queries if str(query).strip()]
    if not queries:
        raise MediaError("At least one non-empty query is required")
    if provider not in {"auto", "pexels", "pixabay", "wikimedia"}:
        raise MediaError(f"Unsupported provider: {provider}")
    providers = [provider] if provider != "auto" else ["pexels", "pixabay", "wikimedia"]
    results: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for source in providers:
        if source == "pexels" and not os.getenv("PEXELS_API_KEY"):
            skipped.append({"provider": source, "reason": "PEXELS_API_KEY not configured"})
            continue
        if source == "pixabay" and not os.getenv("PIXABAY_API_KEY"):
            skipped.append({"provider": source, "reason": "PIXABAY_API_KEY not configured"})
            continue
        for query in queries:
            try:
                if source == "pexels":
                    if media_type not in {"video", "any"}:
                        continue
                    results.extend(search_pexels(query, orientation, per_page))
                elif source == "pixabay":
                    if media_type not in {"video", "any"}:
                        continue
                    results.extend(search_pixabay(query, orientation, per_page))
                else:
                    results.extend(search_wikimedia(query, media_type, per_page))
            except MediaError as exc:
                skipped.append({"provider": source, "reason": str(exc)})
    seen: set[tuple[str, str]] = set()
    unique = []
    for item in results:
        key = (str(item.get("provider")), str(item.get("provider_asset_id")))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return {"queries": queries, "count": len(unique), "results": unique, "providers_skipped": skipped}


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")
    return cleaned[:120] or "asset"


def _extension_from_url(url: str, media_type: str) -> str:
    suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
    allowed = {".mp4", ".mov", ".webm", ".mkv", ".jpg", ".jpeg", ".png", ".webp", ".svg"}
    if suffix in allowed:
        return suffix
    return ".mp4" if media_type == "video" else ".jpg"


def _load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "1.0", "assets": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MediaError(f"Cannot read ledger {path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("assets"), list):
        raise MediaError("Ledger must be an object with an assets array")
    return payload


def _write_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(ledger, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _relative_to_ledger(file_path: Path, ledger_path: Path) -> str:
    try:
        return os.path.relpath(file_path.resolve(), ledger_path.parent.resolve())
    except ValueError:
        return str(file_path.resolve())


def _upsert_asset(ledger_path: Path, entry: dict[str, Any]) -> dict[str, Any]:
    ledger = _load_ledger(ledger_path)
    for existing in ledger["assets"]:
        if existing.get("sha256") == entry.get("sha256") or (
            existing.get("provider") == entry.get("provider")
            and existing.get("provider_asset_id") == entry.get("provider_asset_id")
        ):
            existing_segments = set(existing.get("segment_ids") or [])
            existing_segments.update(entry.get("segment_ids") or [])
            existing.update(entry)
            existing["segment_ids"] = sorted(existing_segments)
            _write_ledger(ledger_path, ledger)
            return existing
    ledger["assets"].append(entry)
    _write_ledger(ledger_path, ledger)
    return entry


def download_media(
    item: dict[str, Any], output_dir: str, ledger_path: str, segment_id: str, filename: str | None = None
) -> dict[str, Any]:
    provider = str(item.get("provider") or "").lower()
    if provider not in REMOTE_PROVIDERS:
        raise MediaError("download_media accepts pexels, pixabay, or wikimedia items")
    url = str(item.get("download_url") or "")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS[provider]:
        raise MediaError(f"Download URL host is not allowed for {provider}: {parsed.hostname}")
    if provider == "wikimedia" and not _commons_license_allowed(str(item.get("license") or "")):
        raise MediaError("Wikimedia item does not have an automatically accepted license")
    required = ("provider_asset_id", "creator", "source_page", "license", "license_url", "attribution")
    missing = [field for field in required if not item.get(field)]
    if missing:
        raise MediaError(f"Candidate is missing rights metadata: {', '.join(missing)}")

    destination_dir = Path(output_dir).expanduser().resolve()
    ledger = Path(ledger_path).expanduser().resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    extension = _extension_from_url(url, str(item.get("media_type") or "video"))
    stem = filename or f"{provider}-{item['provider_asset_id']}"
    destination = destination_dir / f"{_safe_filename(stem)}{extension}"
    if destination.exists():
        raise MediaError(f"Refusing to overwrite existing file: {destination}")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    hasher = hashlib.sha256()
    downloaded = 0
    temporary = destination.with_name(f".{destination.name}.part")
    try:
        with urllib.request.urlopen(req, timeout=60) as response, temporary.open("xb") as handle:
            content_length = int(response.headers.get("Content-Length") or 0)
            if content_length > MAX_DOWNLOAD_BYTES:
                raise MediaError(f"Asset exceeds {MAX_DOWNLOAD_BYTES} bytes")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > MAX_DOWNLOAD_BYTES:
                    raise MediaError(f"Asset exceeds {MAX_DOWNLOAD_BYTES} bytes")
                handle.write(chunk)
                hasher.update(chunk)
        os.replace(temporary, destination)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    digest = hasher.hexdigest()
    entry = {
        "id": f"{provider}:{item['provider_asset_id']}",
        "provider": provider,
        "provider_asset_id": str(item["provider_asset_id"]),
        "creator": str(item["creator"]),
        "source_page": str(item["source_page"]),
        "license": str(item["license"]),
        "license_url": str(item["license_url"]),
        "retrieved_at": _now(),
        "file_path": _relative_to_ledger(destination, ledger),
        "sha256": digest,
        "bytes": downloaded,
        "segment_ids": [segment_id],
        "attribution": str(item["attribution"]),
        "rights_notes": str(item.get("rights_notes") or "Review provider terms before publication."),
        "manual_review_required": bool(item.get("manual_review_required", False)),
        "query": item.get("query"),
    }
    saved = _upsert_asset(ledger, entry)
    return {"ok": True, "file": str(destination), "ledger": str(ledger), "asset": saved}


def register_local_media(
    file_path: str, ledger_path: str, segment_id: str, creator: str, rights_basis: str
) -> dict[str, Any]:
    source = Path(file_path).expanduser().resolve()
    ledger = Path(ledger_path).expanduser().resolve()
    if not source.is_file():
        raise MediaError(f"Local media file does not exist: {source}")
    hasher = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    entry = {
        "id": f"local:{digest[:16]}",
        "provider": "local",
        "provider_asset_id": digest[:16],
        "creator": creator,
        "source_page": f"local:{source.name}",
        "license": "User-supplied media",
        "license_url": "user-attestation",
        "retrieved_at": _now(),
        "file_path": _relative_to_ledger(source, ledger),
        "sha256": digest,
        "bytes": source.stat().st_size,
        "segment_ids": [segment_id],
        "attribution": creator,
        "rights_notes": rights_basis,
        "manual_review_required": not bool(rights_basis.strip()),
    }
    saved = _upsert_asset(ledger, entry)
    return {"ok": True, "ledger": str(ledger), "asset": saved}


def validate_ledger(ledger_path: str, verify_files: bool = False) -> dict[str, Any]:
    path = Path(ledger_path).expanduser().resolve()
    report: dict[str, Any] = {"ok": True, "ledger": str(path), "errors": [], "warnings": [], "assets": 0}
    try:
        ledger = _load_ledger(path)
    except MediaError as exc:
        report["errors"].append(str(exc))
        report["ok"] = False
        return report
    report["assets"] = len(ledger["assets"])
    ids: set[str] = set()
    for index, asset in enumerate(ledger["assets"]):
        label = asset.get("id") or f"asset[{index}]"
        missing = sorted(REQUIRED_LEDGER_FIELDS - set(asset.keys()))
        if missing:
            report["errors"].append(f"{label}: missing fields {', '.join(missing)}")
        if label in ids:
            report["errors"].append(f"{label}: duplicate ledger id")
        ids.add(str(label))
        provider = str(asset.get("provider") or "")
        if provider in REMOTE_PROVIDERS:
            source_page = urllib.parse.urlsplit(str(asset.get("source_page") or ""))
            license_page = urllib.parse.urlsplit(str(asset.get("license_url") or ""))
            if source_page.scheme != "https" or not source_page.netloc:
                report["errors"].append(f"{label}: remote source_page must be a stable HTTPS page")
            if license_page.scheme != "https" or not license_page.netloc:
                report["errors"].append(f"{label}: remote license_url must be HTTPS")
        if provider == "wikimedia" and not _commons_license_allowed(str(asset.get("license") or "")):
            report["errors"].append(f"{label}: Wikimedia license is not automatically accepted")
        if asset.get("manual_review_required"):
            report["warnings"].append(f"{label}: manual rights/context review required")
        if verify_files and asset.get("file_path"):
            candidate = Path(str(asset["file_path"]))
            if not candidate.is_absolute():
                candidate = path.parent / candidate
            if not candidate.is_file():
                report["errors"].append(f"{label}: file missing at {candidate}")
            else:
                hasher = hashlib.sha256()
                with candidate.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        hasher.update(chunk)
                if hasher.hexdigest() != asset.get("sha256"):
                    report["errors"].append(f"{label}: SHA-256 mismatch")
    report["ok"] = not report["errors"]
    return report


def _read_item(value: str) -> dict[str, Any]:
    candidate = Path(value)
    text = candidate.read_text(encoding="utf-8") if candidate.is_file() else value
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise MediaError("Item must be a JSON object")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("queries", nargs="+")
    search.add_argument("--provider", default="auto", choices=["auto", "pexels", "pixabay", "wikimedia"])
    search.add_argument("--orientation", default="landscape", choices=["landscape", "portrait", "square", "any"])
    search.add_argument("--media-type", default="video", choices=["video", "image", "any"])
    search.add_argument("--per-page", type=int, default=8)
    download = sub.add_parser("download")
    download.add_argument("--item", required=True, help="JSON object or path to JSON file")
    download.add_argument("--output-dir", required=True)
    download.add_argument("--ledger", required=True)
    download.add_argument("--segment-id", required=True)
    download.add_argument("--filename")
    local = sub.add_parser("register-local")
    local.add_argument("--file", required=True)
    local.add_argument("--ledger", required=True)
    local.add_argument("--segment-id", required=True)
    local.add_argument("--creator", required=True)
    local.add_argument("--rights-basis", required=True)
    validate = sub.add_parser("validate-ledger")
    validate.add_argument("--ledger", required=True)
    validate.add_argument("--verify-files", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "search":
            result = search_media(args.queries, args.provider, args.orientation, args.media_type, args.per_page)
        elif args.command == "download":
            result = download_media(_read_item(args.item), args.output_dir, args.ledger, args.segment_id, args.filename)
        elif args.command == "register-local":
            result = register_local_media(args.file, args.ledger, args.segment_id, args.creator, args.rights_basis)
        else:
            result = validate_ledger(args.ledger, args.verify_files)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 1
    except (MediaError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
