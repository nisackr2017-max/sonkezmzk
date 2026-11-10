# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR


import shutil
import time
from pathlib import Path

from KumsalTR import logger


def ensure_dirs():
    """
    Ensure that the necessary directories exist.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg must be installed and accessible in the system PATH.")
    if not (shutil.which("deno") or shutil.which("node")):
        logger.warning(
            "Deno/Node bulunamadı — YouTube JS/PO token üretimi çalışmayabilir."
        )

    for dir in ["cache", "downloads", "KumsalTR/cookies"]:
        Path(dir).mkdir(parents=True, exist_ok=True)
    logger.info("Cache directories updated.")


def cleanup_downloads(max_age_sec: int = 7200, max_bytes: int = 400 * 1024 * 1024) -> int:
    """Railway diskini doldurmamak için eski/indirilen dosyaları siler."""
    root = Path("downloads")
    if not root.exists():
        return 0
    now = time.time()
    removed = 0
    files = [p for p in root.rglob("*") if p.is_file()]
    for p in files:
        try:
            if now - p.stat().st_mtime > max_age_sec:
                p.unlink(missing_ok=True)
                removed += 1
        except OSError:
            pass
    files = [p for p in root.rglob("*") if p.is_file()]
    try:
        total = sum(p.stat().st_size for p in files)
    except OSError:
        return removed
    if total <= max_bytes:
        return removed
    for p in sorted(files, key=lambda x: x.stat().st_mtime):
        try:
            total -= p.stat().st_size
            p.unlink(missing_ok=True)
            removed += 1
        except OSError:
            continue
        if total <= max_bytes:
            break
    return removed
