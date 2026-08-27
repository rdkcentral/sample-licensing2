#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator (Clean & Non-Redundant)
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

    issues = data.get("license_issues", []) if isinstance(data, dict) else data
    if not issues:
        sys.exit(0)

    has_issues = False

    for item in issues:
        # 1. Local File & Lines
        local_file_info = item.get("local_file", {})
        local_file = local_file_info.get("path", "Unknown File")
        
        local_blocks = local_file_info.get("highlight", {}).get("blocks", [])
        if local_blocks:
            first_loc = local_blocks[0].get("lines", {})
            local_start = first_loc.get("offset", 1)
            local_len = first_loc.get("length", 1)
            local_end = local_start + local_len - 1
        else:
            local_start, local_end = 1, 1

        # 2. Remote File & Lines
        remote_file_info = item.get("remote_file", {})
        remote_file_path = remote_file_info.get("path", "Remote File")
        
        remote_blocks = remote_file_info.get("highlight", {}).get("blocks", [])
        if remote_blocks:
            first_rem = remote_blocks[0].get("lines", {})
            remote_start = first_rem.get("offset", 1)
            remote_len = first_rem.get("length", 1)
            remote_end = remote_start + remote_len - 1
        else:
            remote_start, remote_end = 1, 1

        # 3. Component & Licenses
        comp = item.get("component", {})
        artifact = comp.get("artifact") or "Unknown Artifact"
        ver = comp.get("version") or ""
        purl = comp.get("purl") or f"{artifact}@{ver}"

        remote_licenses = remote_file_info.get("licenses", [])
        if remote_licenses:
            remote_lic = remote_licenses[0].get("id", "Unknown")
        else:
            comp_licenses = comp.get("license_files", [{}])[0].get("licenses", [])
            remote_lic = comp_licenses[0].get("id", "Unknown") if comp_licenses else "Unknown"

        local_lic = "Apache-2.0"

        # 4. Construct Clickable URL with Range (#L856-L886)
        raw_url = remote_file_info.get("url") or comp.get("url") or "#"
        if "github.com" in raw_url:
            base_url = raw_url.split("#")[0]
            remote_link = f"{base_url}#L{remote_start}-L{remote_end}"
        else:
            remote_link = raw_url

        # 5. Clean, Symmetrical 4-Line Card
        msg = (
            f"Local:     {local_file} (Lines {local_start}-{local_end}) | License: {local_lic}\n"
            f"Remote:    {remote_file_path} (Lines {remote_start}-{remote_end}) | License: {remote_lic}\n"
            f"Component: {purl}\n"
            f"Link:      {remote_link}"
        )

        title = f"FossID Match: {artifact} ({remote_lic})"

        # Emit native GitHub Actions workflow command
        escaped_msg = escape_github_data(msg)
        print(f"::error file={local_file},line={local_start},endLine={local_end},title={title}::{escaped_msg}")
        has_issues = True

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
