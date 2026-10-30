"""Bounded synthetic verification for the approved tiktoken cache relocation."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from unittest.mock import patch

SOURCE = Path("${DATA_ROOT}/codex/cache/tiktoken")
TARGET = Path("${DATA_ROOT}/cache/tiktoken")
ENCODINGS = {
    "o200k_base": "446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d",
    "cl100k_base": "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7",
}


def cache_path(name):
    url = f"https://openaipublic.blob.core.windows.net/encodings/{name}.tiktoken"
    return TARGET / hashlib.sha1(url.encode()).hexdigest()


def snapshot():
    audit = json.loads(Path(__file__).with_name("audit.json").read_text(encoding="utf-8"))
    expected = sorted(audit["source_files"], key=lambda item: item["name"])
    observed = []
    if SOURCE.is_symlink() or not SOURCE.is_dir():
        raise ValueError("source_type_changed")
    for entry in SOURCE.iterdir():
        if not entry.is_file() or entry.is_symlink():
            raise ValueError("unexpected_source_entry")
        stat = entry.stat()
        observed.append({"name": entry.name, "size": stat.st_size,
                         "sha256": hashlib.sha256(entry.read_bytes()).hexdigest(),
                         "last_write_ns": stat.st_mtime_ns})
    if sorted(observed, key=lambda item: item["name"]) != expected:
        raise ValueError("source_changed_since_audit")
    return {"status": "PASS", "check": "original_snapshot_unchanged", "files": len(observed)}


def verify(mode):
    configured = os.environ.get("TIKTOKEN_CACHE_DIR", "")
    if os.path.normcase(os.path.abspath(configured)) != os.path.normcase(str(TARGET.resolve())):
        raise ValueError("wrong_cache_environment")
    import tiktoken
    import tiktoken.load
    if mode == "cold" and cache_path("cl100k_base").exists():
        raise ValueError("cold_cache_precondition_failed")
    names = ["cl100k_base"] if mode == "cold" else ["o200k_base"]
    if mode == "offline-both":
        names.append("cl100k_base")
    text = "Hello, token cache! 你好，分词缓存。🙂"
    checks = []
    original_read = tiktoken.load.read_file
    if mode == "cold":
        import requests
        original_request = requests.sessions.Session.request
        def bounded_request(session, method, url, **kwargs):
            kwargs.setdefault("timeout", 30)
            return original_request(session, method, url, **kwargs)
        network_guard = patch.object(requests.sessions.Session, "request", bounded_request)
        read_guard = patch.object(tiktoken.load, "read_file", wraps=original_read)
    else:
        from contextlib import nullcontext
        network_guard = nullcontext()
        read_guard = patch.object(tiktoken.load, "read_file",
                                 side_effect=AssertionError("offline_cache_attempted_fetch"))
    with network_guard, read_guard as reader:
        for name in names:
            encoding = tiktoken.get_encoding(name)
            tokens = encoding.encode(text)
            if encoding.decode(tokens) != text:
                raise ValueError("round_trip_failed")
            path = cache_path(name)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != ENCODINGS[name]:
                raise ValueError("encoding_hash_or_location_mismatch")
            checks.append({"encoding": name, "round_trip": "PASS", "cache_sha256": ENCODINGS[name]})
        if mode == "cold":
            expected_url = "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
            if reader.call_count != 1 or reader.call_args.args != (expected_url,):
                raise ValueError("cold_fetch_not_observed")
        elif reader.call_count:
            raise ValueError("offline_cache_attempted_fetch")
    return {"status": "PASS", "mode": mode, "tiktoken_version": importlib.metadata.version("tiktoken"),
            "cache": str(TARGET), "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["snapshot", "warm", "cold", "offline-both"])
    args = parser.parse_args()
    try:
        print(json.dumps(snapshot() if args.mode == "snapshot" else verify(args.mode), ensure_ascii=False))
    except Exception as error:
        # Keep network/configuration details out of the result; no credential URLs.
        print(json.dumps({"status": "FAIL", "code": str(error) if isinstance(error, (ValueError, AssertionError))
                          else type(error).__name__}, ensure_ascii=False))
        raise SystemExit(1)
