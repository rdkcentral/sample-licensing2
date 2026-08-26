#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator
Parses FossID diffscan 'license_issues' JSON and emits native GitHub Actions inline annotations.
"""

import json
import os
import sys

def escape_github_data(text):
    """GitHub Actions requires encoding newlines for multiline annotations."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")

def parse_and_annotate(raw_text):
    if not raw_text or not raw_text.strip():
        sys.exit(0)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        sys.exit(0)

    # FossID diffscan stores findings in 'license_issues'
    issues = data.get("license_issues", []) if isinstance(data, dict) else data

    if not issues:
        sys.exit(0)

    has_issues = False

    for item in issues:
        local_file_info = item.get("local_file", {})
        local_file = local_file_info.get("path", "Unknown File")
        
        # Extract Local Line Ranges from highlight blocks
        blocks = local_file_info.get("highlight", {}).get("blocks", [])
        if blocks:
            first_block_lines = blocks[0].get("lines", {})
            local_start = first_block_lines.get("offset", 1)
            local_len = first_block_lines.get("length", 1)
            local_end = local_start + local_len - 1
        else:
            local_start, local_end = 1, 1

        # Extract Component Info
        comp = item.get("component", {})
        artifact = comp.get("artifact") or "Unknown Artifact"
        ver = comp.get("version") or ""
        purl = comp.get("purl") or f"{artifact}@{ver}"

        # Extract Remote File Info and Clickable Link
        remote_file_info = item.get("remote_file", {})
        remote_link = remote_file_info.get("url") or comp.get("url") or "#"

        # Extract License
        remote_licenses = remote_file_info.get("licenses", [])
        if remote_licenses:
            remote_lic = remote_licenses[0].get("id", "Unknown")
        else:
            comp_licenses = comp.get("license_files", [{}])[0].get("licenses", [])
            remote_lic = comp_licenses[0].get("id", "Unknown") if comp_licenses else "Unknown"

        local_lic = "Apache-2.0"

        # Build custom card text
        msg = (
            f"Local Code: {local_file} (Lines {local_start}-{local_end})\n"
            f"Local License: {local_lic}\n"
            f"Matched Component: {purl}\n"
            f"Matched License: {remote_lic}\n"
            f"Remote Match: {remote_link}"
        )

        title = f"FossID Match: {artifact} ({remote_lic})"

        # Emit native GitHub Actions workflow command
        escaped_msg = escape_github_data(msg)
        print(f"::error file={local_file},line={local_start},endLine={local_end},title={title}::{escaped_msg}")
        has_issues = True

    # Fail the step if issues were detected
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
