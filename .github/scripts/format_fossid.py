#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator (Clean & Non-Redundant)
"""

import json
import os
import sys

def escape_github_data(text):
    """GitHub Actions requires encoding newlines and percent signs for multiline annotations."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")

def escape_github_property(text):
    """GitHub Actions requires encoding colons and commas for command properties."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A").replace(":", "%3A").replace(",", "%2C")

def extract_license_str(container):
    """Extracts all unique license identifiers from a JSON container."""
    if not container or not isinstance(container, dict):
        return ""
    
    lic_data = container.get("licenses")
    if lic_data is None:
        lic_data = container.get("license")
        
    if isinstance(lic_data, str):
        return lic_data.strip()
    elif isinstance(lic_data, list):
        extracted = []
        for lic in lic_data:
            if isinstance(lic, str) and lic.strip():
                extracted.append(lic.strip())
            elif isinstance(lic, dict):
                name = lic.get("id") or lic.get("name") or lic.get("spdx_id") or ""
                if name.strip():
                    extracted.append(name.strip())
        return ", ".join(dict.fromkeys(extracted))
    elif isinstance(lic_data, dict):
        return (lic_data.get("id") or lic_data.get("name") or lic_data.get("spdx_id") or "").strip()
    
    return ""

def extract_all_component_licenses(comp):
    """Extracts and merges licenses across component level and all license_files."""
    if not comp or not isinstance(comp, dict):
        return ""
    
    collected = []
    direct_lic = extract_license_str(comp)
    if direct_lic:
        collected.extend([l.strip() for l in direct_lic.split(",") if l.strip()])
    
    lic_files = comp.get("license_files") or []
    if isinstance(lic_files, list):
        for lf in lic_files:
            if isinstance(lf, dict):
                lf_lic = extract_license_str(lf)
                if lf_lic:
                    collected.extend([l.strip() for l in lf_lic.split(",") if l.strip()])
                    
    return ", ".join(dict.fromkeys(collected))

def parse_and_annotate(raw_text):
    if not raw_text or not raw_text.strip():
        sys.exit(0)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: Invalid JSON input: {e}\n")
        sys.exit(1)

    issues = data.get("license_issues", []) if isinstance(data, dict) else data
    if not issues or not isinstance(issues, list):
        sys.exit(0)

    has_issues = False
    seen_findings = set()

    for item in issues:
        if not isinstance(item, dict):
            continue

        # 1. Local File & Highlight Blocks
        local_file_info = item.get("local_file") or {}
        local_file = local_file_info.get("path") or ""
        local_blocks = (local_file_info.get("highlight") or {}).get("blocks") or []

        # 2. Remote File & Highlight Blocks
        remote_file_info = item.get("remote_file") or {}
        remote_file_path = remote_file_info.get("path") or ""
        remote_blocks = (remote_file_info.get("highlight") or {}).get("blocks") or []

        # Collect all remote line ranges for accurate display and deduplication
        remote_range_strs = []
        for rb in remote_blocks:
            if isinstance(rb, dict):
                rl = rb.get("lines") or {}
                r_start = rl.get("offset")
                r_len = rl.get("length")
                if r_start is not None and r_len is not None:
                    r_end = r_start + (r_len - 1 if r_len > 0 else 0)
                    remote_range_strs.append(f"{r_start}-{r_end}")

        remote_lines_display = f" (Lines {', '.join(remote_range_strs)})" if remote_range_strs else ""

        # 3. Component & Licenses
        comp = item.get("component") or {}
        artifact = comp.get("artifact") or ""
        ver = comp.get("version") or ""
        purl = comp.get("purl") or (f"{artifact}@{ver}" if (artifact and ver) else artifact)

        local_lic = extract_license_str(local_file_info)
        remote_lic = extract_license_str(remote_file_info)
        if not remote_lic:
            remote_lic = extract_all_component_licenses(comp)

        # 4. Construct Clickable URL with Range (#L856-L886)
        raw_url = remote_file_info.get("url") or comp.get("url") or ""
        if raw_url and "github.com" in raw_url and remote_blocks:
            first_rb = remote_blocks[0] if isinstance(remote_blocks[0], dict) else {}
            rl = first_rb.get("lines") or {}
            r_start = rl.get("offset")
            r_len = rl.get("length")
            if r_start is not None and r_len is not None:
                r_end = r_start + (r_len - 1 if r_len > 0 else 0)
                base_url = raw_url.split("#")[0]
                remote_link = f"{base_url}#L{r_start}-L{r_end}"
            else:
                remote_link = raw_url
        else:
            remote_link = raw_url

        # 5. Handle Annotations (Line-Level vs File-Level)
        if local_blocks:
            for loc_b in local_blocks:
                if not isinstance(loc_b, dict):
                    continue

                loc_lines = loc_b.get("lines") or {}
                local_start = loc_lines.get("offset")
                local_len = loc_lines.get("length")
                if local_start is None or local_len is None:
                    continue
                local_end = local_start + (local_len - 1 if local_len > 0 else 0)

                # Deduplication: preserves distinct remote snippets even if local lines match
                dedup_key = (
                    local_file,
                    local_start,
                    local_end,
                    purl,
                    remote_file_path,
                    remote_lic,
                    tuple(remote_range_strs),
                )
                if dedup_key in seen_findings:
                    continue
                seen_findings.add(dedup_key)

                # Format Message
                local_lic_part = f" | License: {local_lic}" if local_lic else ""
                remote_lic_part = f" | License: {remote_lic}" if remote_lic else ""

                msg = (
                    f"Local:     {local_file} (Lines {local_start}-{local_end}){local_lic_part}\n"
                    f"Remote:    {remote_file_path}{remote_lines_display}{remote_lic_part}\n"
                    f"Component: {purl}\n"
                    f"Link:      {remote_link}"
                )

                # Title
                if artifact and remote_lic:
                    title = f"FossID Match: {artifact} ({remote_lic})"
                elif artifact:
                    title = f"FossID Match: {artifact}"
                elif remote_lic:
                    title = f"FossID Match: ({remote_lic})"
                else:
                    title = "FossID Match"

                escaped_msg = escape_github_data(msg)
                escaped_title = escape_github_property(title)
                escaped_file = escape_github_property(local_file)
                print(f"::error file={escaped_file},line={local_start},endLine={local_end},title={escaped_title}::{escaped_msg}")
                has_issues = True
        else:
            # File-level annotation (omits line properties when no local blocks exist)
            dedup_key = (
                local_file,
                None,
                None,
                purl,
                remote_file_path,
                remote_lic,
                tuple(remote_range_strs),
            )
            if dedup_key not in seen_findings:
                seen_findings.add(dedup_key)

                local_lic_part = f" | License: {local_lic}" if local_lic else ""
                remote_lic_part = f" | License: {remote_lic}" if remote_lic else ""

                msg = (
                    f"Local:     {local_file}{local_lic_part}\n"
                    f"Remote:    {remote_file_path}{remote_lines_display}{remote_lic_part}\n"
                    f"Component: {purl}\n"
                    f"Link:      {remote_link}"
                )

                if artifact and remote_lic:
                    title = f"FossID Match: {artifact} ({remote_lic})"
                elif artifact:
                    title = f"FossID Match: {artifact}"
                elif remote_lic:
                    title = f"FossID Match: ({remote_lic})"
                else:
                    title = "FossID Match"

                escaped_msg = escape_github_data(msg)
                escaped_title = escape_github_property(title)
                escaped_file = escape_github_property(local_file)
                print(f"::error file={escaped_file},title={escaped_title}::{escaped_msg}")
                has_issues = True

    if has_issues:
        sys.exit(1)

def main():
    if len(sys.argv) > 1:
        if not os.path.exists(sys.argv[1]):
            sys.stderr.write(f"Error: File not found: {sys.argv[1]}\n")
            sys.exit(1)
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            raw_input = f.read()
    else:
        raw_input = sys.stdin.read()

    parse_and_annotate(raw_input)

if __name__ == "__main__":
    main()
