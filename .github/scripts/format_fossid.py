#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator & SARIF Exporter
"""
import hashlib
import json
import os
import re
import sys
from urllib.parse import quote


def escape_github_data(text):
    """GitHub Actions requires encoding newlines and percent signs for multiline annotations."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def escape_github_property(text):
    """GitHub Actions requires encoding colons and commas for command properties."""
    return (
        text.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


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

    lic_data = container.get("licenses") if container.get("licenses") is not None else container.get("license")
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

    for lf in comp.get("license_files") or []:
        if isinstance(lf, dict):
            lf_lic = extract_license_str(lf)
            if lf_lic:
                collected.extend([l.strip() for l in lf_lic.split(",") if l.strip()])

    return ", ".join(dict.fromkeys(collected))


def get_rule_id(match_type, author, artifact):
    """
    Creates a clean, stable Rule ID compliant with GitHub SARIF requirements.
    """
    comp_clean = re.sub(r"[^a-zA-Z0-9._-]", "-", f"{author}-{artifact}".strip("-"))
    comp_clean = comp_clean if comp_clean else "unspecified"
    match_clean = re.sub(r"[^a-zA-Z0-9._-]", "-", match_type) or "license"
    return f"fossid/{match_clean}/{comp_clean}"


def generate_fingerprint(local_file, artifact, remote_file_path):
    """
    Custom metadata fingerprint for component tracking.
    """
    identity = f"{local_file}::{artifact}::{remote_file_path}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def write_sarif(path, rules, results):
    """Outputs a SARIF 2.1.0 JSON file compatible with GitHub Code Scanning."""
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "FossID",
                        "organization": "FossID",
                        "informationUri": "https://fossid.com/",
                        "rules": list(rules.values()),
                    }
                },
                "automationDetails": {
                    "id": "fossid-license-compliance/"
                },
                "results": results,
            }
        ],
    }
    with open(path, "w", encoding="utf-8") as sarif_file:
        json.dump(sarif, sarif_file, indent=2)
        sarif_file.write("\n")


def parse_and_annotate(raw_text, sarif_path=None):
    if not raw_text or not raw_text.strip():
        if sarif_path:
            write_sarif(sarif_path, {}, [])
        sys.exit(0)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: Invalid JSON input: {e}\n")
        sys.exit(1)

    issues = data.get("license_issues", []) if isinstance(data, dict) else data
    if not issues or not isinstance(issues, list):
        if sarif_path:
            write_sarif(sarif_path, {}, [])
        sys.exit(0)

    seen_findings = set()
    seen_sarif_findings = set()
    sarif_rules = {}
    sarif_results = []
    has_issues = False

    for item in issues:
        if not isinstance(item, dict):
            continue

        # 1. Metadata Extraction
        local_file_info = item.get("local_file") or {}
        local_file = local_file_info.get("path") or ""
        local_blocks = (local_file_info.get("highlight") or {}).get("blocks") or []

        remote_file_info = item.get("remote_file") or {}
        remote_file_path = remote_file_info.get("path") or ""
        remote_blocks = (remote_file_info.get("highlight") or {}).get("blocks") or []

        comp = item.get("component") or {}
        author = comp.get("author") or ""
        artifact = comp.get("artifact") or ""
        ver = comp.get("version") or ""
        purl = comp.get("purl") or (f"{artifact}@{ver}" if (artifact and ver) else artifact)
        match_type = item.get("match_type") or "license"

        local_lic = extract_license_str(local_file_info)
        remote_lic = extract_license_str(remote_file_info) or extract_all_component_licenses(comp)
        raw_url = remote_file_info.get("url") or comp.get("url") or ""

        # 2. Extract block positions
        valid_local_blocks = []
        for b in local_blocks:
            if isinstance(b, dict):
                lines = b.get("lines") or {}
                start = lines.get("offset")
                length = lines.get("length")
                if start is not None and length is not None:
                    start_line = start + 1
                    valid_local_blocks.append((start_line, start_line + (length - 1 if length > 0 else 0)))

        tasks = []
        if valid_local_blocks:
            for idx, (l_start, l_end) in enumerate(valid_local_blocks):
                is_last = (idx == len(valid_local_blocks) - 1)
                rem_slice = remote_blocks[idx:] if is_last else ([remote_blocks[idx]] if idx < len(remote_blocks) else [])
                tasks.append((l_start, l_end, rem_slice))
        else:
            tasks.append((1, 1, remote_blocks))

        # 3. Process matches and build annotations & SARIF results
        for local_start, local_end, rem_slice in tasks:
            rem_ranges = []
            for rb in rem_slice:
                if isinstance(rb, dict):
                    rl = rb.get("lines") or {}
                    r_start = rl.get("offset")
                    r_len = rl.get("length")
                    if r_start is not None and r_len is not None:
                        start_line = r_start + 1
                        rem_ranges.append((start_line, start_line + (r_len - 1 if r_len > 0 else 0)))

            rem_range_strs = [f"{s}-{e}" for s, e in rem_ranges]
            remote_lines_display = f" (Lines {', '.join(rem_range_strs)})" if rem_range_strs else ""

            # Deduplicate items
            dedup_key = (local_file, local_start, local_end, purl, remote_file_path, remote_lic, tuple(rem_range_strs))
            if dedup_key in seen_findings:
                continue
            seen_findings.add(dedup_key)

            # Build links
            primary_r_start, primary_r_end = rem_ranges[0] if rem_ranges else (None, None)
            if raw_url and "github.com" in raw_url:
                base_url = raw_url.split("#")[0]
                remote_link = f"{base_url}#L{primary_r_start}-L{primary_r_end}" if primary_r_start is not None else base_url
            else:
                remote_link = raw_url

            local_link = get_local_link(local_file, local_start, local_end)

            local_line_str = f" (Lines {local_start}-{local_end})" if local_start is not None else ""
            local_lic_part = f" | License: {local_lic}" if local_lic else ""
            remote_lic_part = f" | License: {remote_lic}" if remote_lic else ""

            link_section = f"Local Link:  {local_link}\nRemote Link: {remote_link}" if local_link else f"Link:        {remote_link}"

            msg = (
                f"Local:       {local_file}{local_line_str}{local_lic_part}\n"
                f"Remote:      {remote_file_path}{remote_lines_display}{remote_lic_part}\n"
                f"Component:   {purl}\n"
                f"{link_section}"
            )

            # Build SARIF result if requested
            if sarif_path and local_file:
                rule_id = get_rule_id(match_type, author, artifact)
                sarif_key = (local_file, local_start, rule_id)

                if sarif_key not in seen_sarif_findings:
                    seen_sarif_findings.add(sarif_key)

                    rule_desc = f"FossID detected code matching component '{artifact or 'third-party'}' ({remote_lic or 'unknown license'})."
                    sarif_rules.setdefault(
                        rule_id,
                        {
                            "id": rule_id,
                            "name": "FossIDLicenseMatch",
                            "shortDescription": {"text": f"Third-party match: {artifact or 'External Component'}"},
                            "fullDescription": {"text": rule_desc},
                            "help": {
                                "text": f"Component: {purl}\nLicense: {remote_lic}\nRemote: {remote_file_path}",
                                "markdown": (
                                    f"### FossID Third-Party Match\n\n"
                                    f"- **Component:** `{purl}`\n"
                                    f"- **Matched License:** `{remote_lic or 'Unknown'}`\n"
                                    f"- **Local License:** `{local_lic or 'Not stated'}`\n"
                                    f"- **Remote Source:** [{remote_file_path}]({remote_link})\n\n"
                                    f"If this match is approved or an acceptable false positive, "
                                    f"dismiss it with a comment in this Code Scanning alert."
                                ),
                            },
                            # Marked as error
                            "defaultConfiguration": {"level": "error"},
                            "properties": {"tags": ["license-compliance", "fossid"]},
                        },
                    )

                    # Store our identifier in correlationKey to prevent conflicts with GitHub's primaryLocationLineHash
                    match_fingerprint = generate_fingerprint(local_file, artifact, remote_file_path)

                    sarif_results.append(
                        {
                            "ruleId": rule_id,
                            "level": "error",  # Marked as error
                            "message": {"text": msg},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": local_file,
                                            "uriBaseId": "%SRCROOT%"
                                        },
                                        "region": {
                                            "startLine": local_start or 1,
                                            "endLine": local_end or local_start or 1
                                        },
                                    }
                                }
                            ],
                            # GitHub will auto-populate primaryLocationLineHash correctly
                            "correlationId": match_fingerprint,
                        }
                    )

            # Workflow inline annotation command (marked as error)
            title_comp = f"{artifact} ({remote_lic})" if (artifact and remote_lic) else (artifact or (f"({remote_lic})" if remote_lic else ""))
            title = f"FossID Match: {title_comp}" if title_comp else "FossID Match"

            escaped_msg = escape_github_data(msg)
            escaped_title = escape_github_property(title)
            escaped_file = escape_github_property(local_file)

            line_props = f",line={local_start},endLine={local_end}" if local_start is not None else ""
            print(f"::error file={escaped_file}{line_props},title={escaped_title}::{escaped_msg}")
            has_issues = True

    if sarif_path:
        write_sarif(sarif_path, sarif_rules, sarif_results)

    sys.exit(0)


def main():
    input_path = None
    sarif_path = None
    args = iter(sys.argv[1:])
    for arg in args:
        if arg == "--sarif":
            try:
                sarif_path = next(args)
            except StopIteration:
                sys.stderr.write("Error: --sarif requires an output path\n")
                sys.exit(2)
        elif input_path is None:
            input_path = arg
        else:
            sys.stderr.write(f"Error: Unexpected argument: {arg}\n")
            sys.exit(2)

    if input_path:
        if not os.path.exists(input_path):
            sys.stderr.write(f"Error: File not found: {input_path}\n")
            sys.exit(1)
        with open(input_path, "r", encoding="utf-8") as f:
            raw_input = f.read()
    else:
        raw_input = sys.stdin.read()

    parse_and_annotate(raw_input, sarif_path)


if __name__ == "__main__":
    main()
