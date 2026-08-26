#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator
Reads diffscan JSON and emits native GitHub Actions inline annotations
pinned to the exact modified lines in the 'Files changed' tab.
"""

import json
import os
import sys

def escape_github_data(text):
    """GitHub Actions requires encoding newlines for multiline annotations."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")

def parse_and_annotate(json_text):
    # Exit cleanly if input is empty
    if not json_text or not json_text.strip():
        sys.exit(0)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        sys.exit(0)

    matches = data if isinstance(data, list) else data.get("matches", data.get("files", []))
    
    # Exit cleanly if no matches found (0 issues)
    if not matches:
        sys.exit(0)

    has_issues = False

    for item in matches:
        local_file = item.get("file") or item.get("local_path", "Unknown File")
        comp = item.get("component", {})
        artifact = comp.get("artifact") or "Unknown Artifact"
        purl = comp.get("purl", "")
        base_url = comp.get("url", "")
        author = comp.get("author", "")
        ver = comp.get("version", "")

        # Extract local and remote licenses
        local_lic = item.get("file_license") or item.get("declared_license") or "Apache-2.0"
        remote_lic = comp.get("license") or "Unknown"

        # Calculate exact line ranges
        snippet = item.get("snippet", {})
        local_start = item.get("line", 1)
        local_count = snippet.get("local_size", 1)
        local_end = local_start + local_count - 1

        remote_start = item.get("remote_line", 1)
        remote_count = snippet.get("remote_size", local_count)
        remote_end = remote_start + remote_count - 1

        remote_file = item.get("remote_file") or item.get("file", {}).get("path", "")

        # Build clickable line-range link for GitHub
        if "github.com" in base_url and author and artifact and ver and remote_file:
            remote_link = f"https://github.com/{author}/{artifact}/blob/{ver}/{remote_file}#L{remote_start}-L{remote_end}"
        elif base_url:
            remote_link = base_url
        else:
            remote_link = "#"

        display_component = purl if purl else f"{artifact}@{ver}"

        # Card body displayed inside the inline annotation box
        msg = (
            f"Local Code: {local_file} (Lines {local_start}-{local_end})\n"
            f"Local License: {local_lic}\n"
            f"Matched Component: {display_component}\n"
            f"Matched License: {remote_lic}\n"
            f"Remote Match: {remote_link}"
        )

        title = f"FossID Match: {artifact} ({remote_lic})"

        # Emit native GitHub Actions workflow command
        # GitHub automatically attaches this inline on 'Files changed' at lines local_start to local_end
        escaped_msg = escape_github_data(msg)
        print(f"::error file={local_file},line={local_start},endLine={local_end},title={title}::{escaped_msg}")
        has_issues = True

    # Fail the step if issues were detected (enforces the PR security gate)
    if has_issues:
        sys.exit(1)

def main():
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            raw_input = f.read()
    else:
        raw_input = sys.stdin.read()

    parse_and_annotate(raw_input)

if __name__ == "__main__":
    main()
