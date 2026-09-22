#!/usr/bin/env python3
"""
FossID Native GitHub Inline Annotator & SARIF Exporter
Schema-compliant SARIF 2.1.0
"""
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
    """Escape control characters and separators for GitHub Actions parameters."""
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
    if start_line is not None:
        return f"{base}#L{start_line}"
    return base


def get_remote_link(raw_url: str, remote_blocks: List[Tuple[int, int]]) -> str:
    """Construct an upstream URL linking directly to the first highlight range."""
    if not raw_url:
        return ""
    start, end = remote_blocks[0] if remote_blocks else (None, None)
    if "github.com" in raw_url:
        base_url = raw_url.split("#")[0]
        return f"{base_url}#L{start}-L{end}" if start is not None else base_url
    return raw_url


def extract_license_str(container: Any) -> str:
    """Extract unique license IDs from a FossID container's `licenses` list."""
    if not isinstance(container, dict):
        return ""
    names: List[str] = [
        lic["id"].strip()
        for lic in container.get("licenses") or []
        if isinstance(lic, dict) and lic.get("id")
    ]
    return ", ".join(dict.fromkeys(names))


def extract_all_component_licenses(comp: Any) -> str:
    """Extract and merge licenses across component root and all license_files."""
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


def get_rule_id(
    match_type: str, author: str, artifact: str, version: str = ""
) -> str:
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
    match_clean = (
        re.sub(r"[^a-z0-9._-]", "-", match_type.lower())
        if match_type
        else "partial"
    )
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
                        "description": {
                            "text": "The root of the source repository."
                        }
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
    """Convert FossID highlight blocks (0-based) to 1-based (start, end) lines."""
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


def build_card_message(
    local_file: str,
    local_range: Tuple[Optional[int], Optional[int]],
    rem_lines_display: str,
    meta: Dict[str, Any],
    remote_link: str,
) -> str:
    """Construct formatted text card for inline annotations and SARIF."""
    start, end = local_range
    local_link = get_local_link(local_file, start, end)
    local_line_str = (
        f" (Lines {start}-{end})" if start is not None else " (entire file)"
    )
    lic_part = (
        f" | License: {meta['remote_lic']}" if meta["remote_lic"] else ""
    )

    link_section = (
        f"Local Link:  {local_link}\nRemote Link: {remote_link}"
        if local_link
        else f"Link:        {remote_link}"
    )

    return (
        f"Local:       {local_file}{local_line_str}\n"
        f"Remote:      {meta['remote_file']}{rem_lines_display}{lic_part}\n"
        f"Component:   {meta['purl']}\n"
        f"Match Type:  {meta['match_display']}\n"
        f"{link_section}"
    )


def register_sarif_finding(
    sarif_rules: Dict[str, Any],
    sarif_results: List[Dict[str, Any]],
    meta: Dict[str, Any],
    card_msg: str,
    local_range: Tuple[Optional[int], Optional[int]],
) -> None:
    """Register SARIF rule definition and individual finding result."""
    rule_id = get_rule_id(
        meta["raw_match_type"], meta["author"], meta["artifact"], meta["ver"]
    )
    match_display = meta["match_display"]
    art = meta["artifact"] or "External Component"

    sarif_rules.setdefault(
        rule_id,
        {
            "id": rule_id,
            "name": "FossIDLicenseMatch",
            "shortDescription": {"text": f"Third-party {match_display}: {art}"},
            "fullDescription": {
                "text": (
                    f"FossID detected a {match_display.lower()} against the "
                    f"third-party component '{art}'."
                )
            },
            "help": {
                "text": (
                    f"Third-party {match_display} for component '{art}'. "
                    "Verify this component complies with open-source policy."
                ),
                "markdown": (
                    f"### FossID Third-Party {match_display}\n\n"
                    f"- **Component:** `{art}`\n\n"
                    "**Compliance Policy:**\n"
                    "Verify that this external component and its license terms "
                    "comply with project open-source guidelines."
                ),
            },
            "defaultConfiguration": {"level": "error"},
            "properties": {"tags": ["license-compliance", "fossid"]},
        },
    )

    phys_loc: Dict[str, Any] = {
        "artifactLocation": {
            "uri": meta["local_file"],
            "uriBaseId": "%SRCROOT%",
        }
    }
    start, end = local_range
    if start is not None:
        phys_loc["region"] = {"startLine": start, "endLine": end or start}

    sarif_results.append(
        {
            "ruleId": rule_id,
            "level": "error",
            "message": {"text": card_msg},
            "locations": [{"physicalLocation": phys_loc}],
            "properties": {
                "component": meta["purl"],
                "remoteFile": meta["remote_file"],
                "matchType": match_display,
                "matchedLicense": meta["remote_lic"],
            },
        }
    )


def emit_github_annotation(
    local_file: str,
    local_range: Tuple[Optional[int], Optional[int]],
    meta: Dict[str, Any],
    card_msg: str,
) -> None:
    """Print the escaped GitHub Actions workflow inline annotation command."""
    lic_tag = f"({meta['remote_lic']})" if meta["remote_lic"] else ""
    parts = [p for p in [meta["artifact"], lic_tag] if p]
    title_comp = " ".join(parts)
    title = (
        f"FossID {meta['match_display']}: {title_comp}"
        if title_comp
        else f"FossID {meta['match_display']}"
    )

    escaped_msg = escape_github_data(card_msg)
    escaped_title = escape_github_property(title)

    file_prop = (
        f"file={escape_github_property(local_file)}," if local_file else ""
    )
    start, end = local_range
    line_props = (
        f"line={start},endLine={end}," if start is not None else ""
    )

    print(
        f"::error {file_prop}{line_props}title={escaped_title}::{escaped_msg}"
    )


def extract_metadata(
    item: Dict[str, Any], local_file: str, remote_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract and normalize finding metadata into a dictionary."""
    comp = item.get("component") or {}
    raw_match_type = item.get("match_type") or "partial"
    art = comp.get("artifact") or ""
    ver = comp.get("version") or ""
    fallback_purl = f"{art}@{ver}" if (art and ver) else art

    # Dual-layer resolution: check matched file first, fall back to upstream project license files
    remote_lic = (
        extract_license_str(remote_info)
        or extract_all_component_licenses(comp)
    )

    return {
        "local_file": local_file,
        "remote_file": remote_info.get("path") or "",
        "author": comp.get("author") or "",
        "artifact": art,
        "ver": ver,
        "purl": comp.get("purl") or fallback_purl,
        "raw_match_type": raw_match_type,
        "match_display": MATCH_TYPE_LABELS.get(
            raw_match_type.lower(), f"{raw_match_type} Match"
        ),
        "remote_lic": remote_lic,
        "raw_url": remote_info.get("url") or comp.get("url") or "",
    }


def resolve_local_blocks(
    valid_local: List[Tuple[int, int]],
    match_type: str,
    local_file: str,
) -> Optional[List[Tuple[Optional[int], Optional[int]]]]:
    """Return normalized line ranges or None if finding is anomalous and skippable."""
    if valid_local:
        return list(valid_local)
    if match_type.lower() == "file":
        return [(None, None)]

    sys.stderr.write(
        f"Warning: skipping '{match_type}' match for "
        f"{local_file or 'unknown file'} with no valid local range\n"
    )
    return None


def process_single_issue(
    item: Dict[str, Any],
    sarif_rules: Dict[str, Any],
    sarif_results: List[Dict[str, Any]],
    emit_sarif: bool,
) -> None:
    """Parse one FossID issue, print annotations, and append SARIF objects."""
    local_info = item.get("local_file") or {}
    local_file = local_info.get("path") or ""
    remote_info = item.get("remote_file") or {}

    valid_local = _line_ranges(
        (local_info.get("highlight") or {}).get("blocks")
    )
    valid_remote = _line_ranges(
        (remote_info.get("highlight") or {}).get("blocks")
    )

    meta = extract_metadata(item, local_file, remote_info)
    target_local_blocks = resolve_local_blocks(
        valid_local, meta["raw_match_type"], local_file
    )
    if target_local_blocks is None:
        return

    rem_range_strs = [f"{s}-{e}" for s, e in valid_remote]
    rem_lines_display = (
        f" (Lines {', '.join(rem_range_strs)})" if rem_range_strs else ""
    )
    remote_link = get_remote_link(meta["raw_url"], valid_remote)

    for local_range in target_local_blocks:
        card_msg = build_card_message(
            local_file, local_range, rem_lines_display, meta, remote_link
        )

        if emit_sarif and local_file:
            register_sarif_finding(
                sarif_rules, sarif_results, meta, card_msg, local_range
            )

        emit_github_annotation(local_file, local_range, meta, card_msg)


def parse_and_annotate(
    raw_text: str, sarif_path: Optional[str] = None
) -> None:
    """Parse FossID JSON, print inline GitHub annotations, and write SARIF."""
    if not raw_text or not raw_text.strip():
        if sarif_path:
            write_sarif(sarif_path, {}, [])
        return

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as err:
        sys.stderr.write(f"Error: Invalid JSON input: {err}\n")
        sys.exit(1)

    issues = data.get("license_issues", []) if isinstance(data, dict) else []
    if not issues or not isinstance(issues, list):
        if sarif_path:
            write_sarif(sarif_path, {}, [])
        return

    sarif_rules: Dict[str, Any] = {}
    sarif_results: List[Dict[str, Any]] = []

    for item in issues:
        if isinstance(item, dict):
            process_single_issue(
                item, sarif_rules, sarif_results, bool(sarif_path)
            )

    if sarif_path:
        write_sarif(sarif_path, sarif_rules, sarif_results)


def main() -> None:
    """Parse CLI arguments and run the FossID annotator and SARIF exporter."""
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
        with open(input_path, "r", encoding="utf-8") as file_handle:
            raw_input = file_handle.read()
    else:
        raw_input = sys.stdin.read()

    parse_and_annotate(raw_input, sarif_path)


if __name__ == "__main__":
    main()
