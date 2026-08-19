"""Shared file/folder naming helpers for generated application documents.

Every tool that names an output folder or file (generators, pusher, local
save) must use this sanitizer so a row's artifacts always resolve to the
same folder across generate → push → revise cycles.
"""
import re


def sanitize_path_component(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
