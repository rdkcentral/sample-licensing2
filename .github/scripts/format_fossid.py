#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator
"""

#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator
Universal Block Handler (Handles 1:1, N:M, and File-Level matches)
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

def get_local_link(file_path, start_line=None, end_line=None):
    """Constructs a direct GitHub URL to the exact lines in the local repository."""
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY")
    ref = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_SHA")
    
    if not (repo and ref and file_path):
        return ""
    
    base = f"{server_url}/{repo}/blob/{ref}/{file_path}"
    if start_line is not None and end_line is not None:
        return f"{base}#L{start_line}-L{end_line}"
    elif start_line is not None:
        return f"{base}#L{start_line}"
    return base

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

        # 3. Component & Licenses
        comp = item.get("component") or {}
        artifact = comp.get("artifact") or ""
        ver = comp.get("version") or ""
        purl = comp.get("purl") or (f"{artifact}@{ver}" if (artifact and ver) else artifact)

        local_lic = extract_license_str(local_file_info)
        remote_lic = extract_license_str(remote_file_info)
        if not remote_lic:
            remote_lic = extract_all_component_licenses(comp)

        raw_url = remote_file_info.get("url") or comp.get("url") or ""

        # 4. Handle Annotations
        if local_blocks:
            for idx, loc_b in enumerate(local_blocks):
                if not isinstance(loc_b, dict):
                    continue

                # Local Line Range
                loc_lines = loc_b.get("lines") or {}
                local_start = loc_lines.get("offset")
                local_len = loc_lines.get("length")
                if local_start is None or local_len is None:
                    continue
                local_end = local_start + (local_len - 1 if local_len > 0 else 0)

                # --- Universal Remote Block Resolution ---
                is_last_local = (idx == len(local_blocks) - 1)

                if len(remote_blocks) == len(local_blocks):
                    # Scenario 1: Exact 1-to-1 count
                    rem_slice = [remote_blocks[idx]]
                elif len(remote_blocks) > len(local_blocks):
                    # Scenario 2: More remote blocks than local (e.g. 6 local, 9 remote)
                    if is_last_local:
                        rem_slice = remote_blocks[idx:]  # Bundle all remaining remote blocks
                    else:
                        rem_slice = [remote_blocks[idx]]
                else:
                    # Scenario 3: More local blocks than remote (e.g. 5 local, 1 remote)
                    if idx < len(remote_blocks):
                        rem_slice = [remote_blocks[idx]]
                    else:
                        rem_slice = remote_blocks  # Fallback to all remote blocks so context is preserved

                # Extract line ranges from the selected remote slice
                rem_ranges = []
                for rb in rem_slice:
                    if isinstance(rb, dict):
                        rl = rb.get("lines") or {}
                        r_start = rl.get("offset")
                        r_len = rl.get("length")
                        if r_start is not None and r_len is not None:
                            r_end = r_start + (r_len - 1 if r_len > 0 else 0)
                            rem_ranges.append((r_start, r_end))

                if rem_ranges:
                    remote_range_strs = [f"{s}-{e}" for s, e in rem_ranges]
                    remote_lines_display = f" (Lines {', '.join(remote_range_strs)})"
                    primary_r_start, primary_r_end = rem_ranges[0]
                else:
                    remote_range_strs = []
                    remote_lines_display = ""
                    primary_r_start, primary_r_end = None, None

                # Deduplication
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

                # Construct Clickable Remote URL
                if raw_url and "github.com" in raw_url:
                    base_url = raw_url.split("#")[0]
                    if primary_r_start is not None and primary_r_end is not None:
                        remote_link = f"{base_url}#L{primary_r_start}-L{primary_r_end}"
                    else:
                        remote_link = base_url
                else:
                    remote_link = raw_url

                # Construct Clickable Local URL
                local_link = get_local_link(local_file, local_start, local_end)

                # Format Message
                local_lic_part = f" | License: {local_lic}" if local_lic else ""
                remote_lic_part = f" | License: {remote_lic}" if remote_lic else ""

                if local_link:
                    link_section = (
                        f"Local Link:  {local_link}\n"
                        f"Remote Link: {remote_link}"
                    )
                else:
                    link_section = f"Link:        {remote_link}"

                msg = (
                    f"Local:       {local_file} (Lines {local_start}-{local_end}){local_lic_part}\n"
                    f"Remote:      {remote_file_path}{remote_lines_display}{remote_lic_part}\n"
                    f"Component:   {purl}\n"
                    f"{link_section}"
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
            # Scenario 4: File-level annotation (whole-file match without highlight blocks)
            rem_ranges = []
            for rb in remote_blocks:
                if isinstance(rb, dict):
                    rl = rb.get("lines") or {}
                    r_start = rl.get("offset")
                    r_len = rl.get("length")
                    if r_start is not None and r_len is not None:
                        r_end = r_start + (r_len - 1 if r_len > 0 else 0)
                        rem_ranges.append((r_start, r_end))

            remote_range_strs = [f"{s}-{e}" for s, e in rem_ranges]
            remote_lines_display = f" (Lines {', '.join(remote_range_strs)})" if remote_range_strs else ""
            primary_r_start, primary_r_end = rem_ranges[0] if rem_ranges else (None, None)

            if raw_url and "github.com" in raw_url:
                base_url = raw_url.split("#")[0]
                if primary_r_start is not None and primary_r_end is not None:
                    remote_link = f"{base_url}#L{primary_r_start}-L{primary_r_end}"
                else:
                    remote_link = base_url
            else:
                remote_link = raw_url

            local_link = get_local_link(local_file)

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

                if local_link:
                    link_section = (
                        f"Local Link:  {local_link}\n"
                        f"Remote Link: {remote_link}"
                    )
                else:
                    link_section = f"Link:        {remote_link}"

                msg = (
                    f"Local:       {local_file}{local_lic_part}\n"
                    f"Remote:      {remote_file_path}{remote_lines_display}{remote_lic_part}\n"
                    f"Component:   {purl}\n"
                    f"{link_section}"
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
