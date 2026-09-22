#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator & SARIF Exporter
Schema-compliant SARIF 2.1.0
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


MATCH_TYPE_LABELS = {
    "file": "Full File Match",
    "partial": "Partial Match",
}


def escape_github_data(text: str) -> str:
    """Escape newlines and percent signs for GitHub Actions command payloads."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def escape_github_property(text: str) -> str:
    """Escape colons, commas, newlines, and percent signs for GitHub Actions parameters."""
    return (
        text.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def get_local_link(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> str:
    """Construct a direct GitHub URL to the exact lines in the local repository."""
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


def extract_license_str(container: Any) -> str:
    """Extract all unique license identifiers from a JSON container."""
    if not container or not isinstance(container, dict):
        return ""

    lic_data = container.get("licenses")
    if lic_data is None:
        lic_data = container.get("license")

    if isinstance(lic_data, str):
        return lic_data.strip()
    elif isinstance(lic_data, list):
        extracted: List[str] = []
        for lic in lic_data:
            if isinstance(lic, str) and lic.strip():
                extracted.append(lic.strip())
            elif isinstance(lic, dict):
                name = lic.get("id") or lic.get("name") or lic.get("spdx_id") or ""
                if name.strip():
                    extracted.append(name.strip())
        return ", ".join(dict.fromkeys(extracted))
    elif isinstance(lic_data, dict):
        name = lic_data.get("id") or lic_data.get("name") or lic_data.get("spdx_id") or ""
        return name.strip()
    return ""


def extract_all_component_licenses(comp: Any) -> str:
    """Extract and merge licenses across component level and all license_files."""
    if not comp or not isinstance(comp, dict):
        return ""
    sources: List[Any] = [comp]
    sources.extend(
        lf for lf in (comp.get("license_files") or []) if isinstance(lf, dict)
    )
    collected: List[str] = []
    for source in sources:
        lic = extract_license_str(source)
        if lic:
            collected.extend(part.strip() for part in lic.split(",") if part.strip())
    return ", ".join(dict.fromkeys(collected))


def get_rule_id(match_type: str, author: str, artifact: str, version: str = "") -> str:
    """Create a clean, stable Rule ID compliant with GitHub SARIF requirements."""
    author = (author or "").strip().lower()
    artifact = (artifact or "").strip().lower()
    version = (version or "").strip().lower()

    if author and artifact and artifact.startswith(author):
        clean_name = artifact
    elif author and artifact:
        clean_name = f"{author}-{artifact}"
    else:
        clean_name = artifact or author or "unspecified"

    if version:
        clean_name = f"{clean_name}-{version}"

    clean_name = re.sub(r"[^a-z0-9._-]", "-", clean_name).strip("-")
    if match_type:
        match_clean = re.sub(r"[^a-z0-9._-]", "-", match_type.lower())
    else:
        match_clean = "partial"
    return f"fossid/{match_clean}/{clean_name}"


def write_sarif(
    path: str, rules: Dict[str, Any], results: List[Dict[str, Any]]
) -> None:
    """Output a strictly compliant SARIF 2.1.0 JSON file."""
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
                "originalUriBaseIds": {
                    "%SRCROOT%": {
                        "description": {"text": "The root of the source repository."}
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


def _line_ranges(blocks: Any) -> List[Tuple[int, int]]:
    """Convert FossID highlight blocks (0-based offset+length) to 1-based (start, end) lines."""
    ranges: List[Tuple[int, int]] = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        lines = block.get("lines") or {}
        offset = lines.get("offset")
        length = lines.get("length")
        if offset is None or length is None:
            continue
        start = offset + 1
        ranges.append((start, start + (length - 1 if length > 0 else 0)))
    return ranges


def parse_and_annotate(raw_text: str, sarif_path: Optional[str] = None) -> None:
    """Parse FossID JSON, print inline GitHub annotations, and generate SARIF report."""
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

    sarif_rules: Dict[str, Any] = {}
    sarif_results: List[Dict[str, Any]] = []

    for item in issues:
        if not isinstance(item, dict):
            continue

        local_file_info = item.get("local_file") or {}
        local_file: str = local_file_info.get("path") or ""
        local_blocks = (local_file_info.get("highlight") or {}).get("blocks") or []

        remote_file_info = item.get("remote_file") or {}
        remote_file_path: str = remote_file_info.get("path") or ""
        remote_blocks = (remote_file_info.get("highlight") or {}).get("blocks") or []

        comp = item.get("component") or {}
        author: str = comp.get("author") or ""
        artifact: str = comp.get("artifact") or ""
        ver: str = comp.get("version") or ""
        fallback_purl = f"{artifact}@{ver}" if (artifact and ver) else artifact
        purl: str = comp.get("purl") or fallback_purl
        raw_match_type: str = item.get("match_type") or "partial"
        match_type_display = MATCH_TYPE_LABELS.get(
            raw_match_type.lower(), f"{raw_match_type} Match"
        )

        remote_lic = (
            extract_license_str(remote_file_info)
            or extract_all_component_licenses(comp)
        )
        raw_url: str = remote_file_info.get("url") or comp.get("url") or ""

        # Validate local blocks
        valid_local_blocks: List[Tuple[Optional[int], Optional[int]]] = list(
            _line_ranges(local_blocks)
        )
        valid_remote_blocks = _line_ranges(remote_blocks)

        rem_range_strs = [f"{s}-{e}" for s, e in valid_remote_blocks]
        remote_lines_display = (
            f" (Lines {', '.join(rem_range_strs)})" if rem_range_strs else ""
        )

        # A whole-file match (match_type "file") carries no local highlight; represent
        # it as a single file-level finding rather than a bogus line-1 range.
        if not valid_local_blocks:
            valid_local_blocks = [(None, None)]

        primary_r_start, primary_r_end = (
            valid_remote_blocks[0] if valid_remote_blocks else (None, None)
        )
        if raw_url and "github.com" in raw_url:
            base_url = raw_url.split("#")[0]
            remote_link = (
                f"{base_url}#L{primary_r_start}-L{primary_r_end}"
                if primary_r_start is not None
                else base_url
            )
        else:
            remote_link = raw_url

        for local_start, local_end in valid_local_blocks:
            local_link = get_local_link(local_file, local_start, local_end)

            local_line_str = (
                f" (Lines {local_start}-{local_end})"
                if local_start is not None
                else " (entire file)"
            )
            remote_lic_part = f" | License: {remote_lic}" if remote_lic else ""

            link_section = (
                f"Local Link:  {local_link}\nRemote Link: {remote_link}"
                if local_link
                else f"Link:        {remote_link}"
            )

            card_msg = (
                f"Local:       {local_file}{local_line_str}\n"
                f"Remote:      {remote_file_path}{remote_lines_display}{remote_lic_part}\n"
                f"Component:   {purl}\n"
                f"Match Type:  {match_type_display}\n"
                f"{link_section}"
            )

            if sarif_path and local_file:
                rule_id = get_rule_id(raw_match_type, author, artifact, ver)

                sarif_rules.setdefault(
                    rule_id,
                    {
                        "id": rule_id,
                        "name": "FossIDLicenseMatch",
                        "shortDescription": {
                            "text": f"Third-party {match_type_display}: {artifact or 'External Component'}"
                        },
                        "fullDescription": {
                            "text": (
                                f"FossID detected a {match_type_display.lower()} against the "
                                f"third-party component '{artifact or 'external component'}'."
                            )
                        },
                        "help": {
                            "text": (
                                f"Third-party {match_type_display} for component "
                                f"'{artifact or 'external component'}'. Verify this "
                                "component and its license terms comply with project "
                                "open-source policy. Each alert lists the matched "
                                "version, source lines, and upstream link."
                            ),
                            "markdown": (
                                f"### FossID Third-Party {match_type_display}\n\n"
                                f"- **Component:** `{artifact or 'external component'}`\n\n"
                                "**Compliance Policy:**\n"
                                "Verify that this external component and its license "
                                "terms comply with project open-source guidelines. "
                                "Consult repository maintainers or the compliance team "
                                "if an approved exception applies.\n\n"
                                "_Matched version, license, source lines, and upstream "
                                "link are shown in each individual alert._"
                            ),
                        },
                        "defaultConfiguration": {"level": "error"},
                        "properties": {"tags": ["license-compliance", "fossid"]},
                    },
                )

                physical_location: Dict[str, Any] = {
                    "artifactLocation": {
                        "uri": local_file,
                        "uriBaseId": "%SRCROOT%",
                    }
                }
                if local_start is not None:
                    physical_location["region"] = {
                        "startLine": local_start,
                        "endLine": local_end or local_start,
                    }

                sarif_results.append(
                    {
                        "ruleId": rule_id,
                        "level": "error",
                        "message": {"text": card_msg},
                        "locations": [{"physicalLocation": physical_location}],
                        "properties": {
                            "component": purl,
                            "remoteFile": remote_file_path,
                            "matchType": match_type_display,
                            "matchedLicense": remote_lic,
                        },
                    }
                )

            title_comp = (
                f"{artifact} ({remote_lic})"
                if (artifact and remote_lic)
                else (artifact or (f"({remote_lic})" if remote_lic else ""))
            )
            title = f"FossID {match_type_display}: {title_comp}" if title_comp else "FossID Match"

            escaped_msg = escape_github_data(card_msg)
            escaped_title = escape_github_property(title)
            escaped_file = escape_github_property(local_file)

            line_props = (
                f",line={local_start},endLine={local_end}"
                if local_start is not None
                else ""
            )
            print(
                f"::error file={escaped_file}{line_props},"
                f"title={escaped_title}::{escaped_msg}"
            )

    if sarif_path:
        write_sarif(sarif_path, sarif_rules, sarif_results)

    # Exits 0 so GitHub's native Code Scanning engine controls PR pass/fail gate
    sys.exit(0)


def main() -> None:
    """Parse command-line arguments and run the FossID annotator and SARIF exporter."""
    input_path: Optional[str] = None
    sarif_path: Optional[str] = None
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
