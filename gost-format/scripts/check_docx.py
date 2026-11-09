#!/usr/bin/env python3
"""Check DOCX section geometry and expose OOXML formatting for manual review.

Python 3.10+, standard library only. Never modifies the input document.
Exit 0 means only that the requested geometry passed, not GOST compliance.
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def local(tag):
    return tag.rsplit("}", 1)[-1]


def attributes(node):
    return {} if node is None else {local(k): v for k, v in node.attrib.items()}


def properties(node):
    """Preserve repeated/nested properties without implying inheritance resolution."""
    if node is None:
        return None
    result = {"attributes": attributes(node)} if node.attrib else {}
    for child in node:
        result.setdefault(local(child.tag), []).append(properties(child))
    return result


def twips_to_mm(value):
    return None if value is None else round(int(value) * 25.4 / 1440, 4)


def extract(package, paper_mm, margins_mm, tolerance):
    root = ET.fromstring(package.read("word/document.xml"))
    ns = {"w": root.tag[1:].split("}", 1)[0]}
    if local(root.tag) != "document":
        raise ValueError("word/document.xml is not a Word document")
    parents = {child: parent for parent in root.iter() for child in parent}

    def inside(node, names):
        while node in parents:
            node = parents[node]
            if local(node.tag) in names:
                return True
        return False

    def find(node, path):
        return node.find(path, ns)

    def text(node):
        return "".join(t.text or "" for t in node.findall(".//w:t", ns))

    report = {
        "scope": "Section geometry only; raw formatting is provided for further review.",
        "expected": {"paper_mm": paper_mm, "margins_mm_L_R_T_B": margins_mm,
                     "tolerance_mm": tolerance},
        "geometry_status": "PASS",
        "sections": [],
        "doc_defaults": None,
        "styles": [],
        "paragraphs": [],
        "footers": [],
        "warnings": [],
        "requires_review": [
            "Standard and local requirements, document structure and title page",
            "Effective fonts, theme, style inheritance, spacing and indents",
            "Captions, tables, formulas, references and bibliography",
            "Page fields, continuous numbering and updated table of contents",
            "Rendered final pages, embedded fonts and object positions",
        ],
    }
    historical = {"sectPrChange", "pPrChange", "del", "moveFrom"}
    for node in root.findall(".//w:sectPr", ns):
        if inside(node, historical):
            continue
        size = attributes(find(node, "w:pgSz"))
        margins = attributes(find(node, "w:pgMar"))
        actual = {
            "width": twips_to_mm(size.get("w")),
            "height": twips_to_mm(size.get("h")),
            **{key: twips_to_mm(margins.get(key))
               for key in ["left", "right", "top", "bottom"]},
        }
        expected = dict(zip(["width", "height", "left", "right", "top", "bottom"],
                            list(paper_mm) + list(margins_mm)))
        issues = []
        for key, wanted in expected.items():
            value = actual[key]
            if value is None:
                issues.append({"property": key, "status": "UNKNOWN", "expected_mm": wanted})
            elif abs(value - wanted) > tolerance:
                issues.append({"property": key, "status": "MISMATCH",
                               "expected_mm": wanted, "actual_mm": value})
        if issues:
            report["geometry_status"] = "FAIL"
        gutter = twips_to_mm(margins.get("gutter"))
        if gutter not in (None, 0):
            report["warnings"].append("Nonzero gutter: verify the effective binding margin.")
        cols = attributes(find(node, "w:cols"))
        if cols.get("num", "1") != "1" or find(node, "w:cols/w:col") is not None:
            report["warnings"].append("Custom columns need separate review.")
        report["sections"].append({
            "index": len(report["sections"]) + 1,
            "actual_mm": actual, "orientation": size.get("orient", "portrait"),
            "issues": issues, "raw_sectPr": properties(node),
        })
    if not report["sections"]:
        report["geometry_status"] = "FAIL"
        report["warnings"].append("No section properties; geometry is unknown.")

    names = set(package.namelist())
    if "word/styles.xml" in names:
        styles = ET.fromstring(package.read("word/styles.xml"))
        report["doc_defaults"] = properties(find(styles, "w:docDefaults"))
        for style in styles.findall("w:style", ns):
            report["styles"].append({
                **attributes(style), "name": attributes(find(style, "w:name")).get("val"),
                "basedOn": attributes(find(style, "w:basedOn")).get("val"),
                "pPr": properties(find(style, "w:pPr")),
                "rPr": properties(find(style, "w:rPr")),
            })
    else:
        report["warnings"].append("No styles.xml; effective text formatting is unknown.")

    for index, paragraph in enumerate(root.findall(".//w:p", ns), 1):
        content = text(paragraph)
        if not content.strip():
            continue
        ppr = find(paragraph, "w:pPr")
        run_overrides = []
        for run in paragraph.findall(".//w:r", ns):
            rpr = find(run, "w:rPr")
            if rpr is not None:
                run_overrides.append({"text": text(run), "rPr": properties(rpr)})
        report["paragraphs"].append({
            "index": index, "text": content,
            "in_table": inside(paragraph, {"tbl"}),
            "style": attributes(find(paragraph, "w:pPr/w:pStyle")).get("val"),
            "pPr": properties(ppr), "run_overrides": run_overrides,
        })

    for name in sorted(names):
        if name.startswith("word/footer") and name.endswith(".xml"):
            footer = ET.fromstring(package.read(name))
            report["footers"].append({
                "part": name, "text": text(footer),
                "complex_field_instructions": [t.text or "" for t in footer.findall(".//w:instrText", ns)],
                "simple_fields": [attributes(t).get("instr") for t in footer.findall(".//w:fldSimple", ns)],
                "paragraph_properties": [properties(t) for t in footer.findall(".//w:pPr", ns)],
            })
    if "word/settings.xml" in names:
        settings = ET.fromstring(package.read("word/settings.xml"))
        report["layout_settings"] = {
            local(t.tag): properties(t) for t in settings
            if local(t.tag) in {"mirrorMargins", "gutterAtTop", "evenAndOddHeaders", "updateFields"}
        }
        if any(local(t.tag) in {"mirrorMargins", "gutterAtTop"} for t in settings):
            report["warnings"].append("Binding/mirror settings are present; inspect their values and effective layout.")
    review_tags = {"ins", "del", "moveFrom", "moveTo", "pPrChange", "rPrChange", "sectPrChange", "txbxContent", "altChunk"}
    present = sorted({local(t.tag) for t in root.iter()} & review_tags)
    if present:
        report["warnings"].append("Review nontrivial content/revisions: " + ", ".join(present))
    report["warnings"] = sorted(set(report["warnings"]))
    return report


def positive(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--paper-mm", nargs=2, type=positive, default=[210, 297], metavar=("WIDTH", "HEIGHT"))
    parser.add_argument("--margins-mm", nargs=4, type=positive, default=[30, 15, 20, 20], metavar=("LEFT", "RIGHT", "TOP", "BOTTOM"))
    parser.add_argument("--tolerance-mm", type=positive, default=0.15)
    parser.add_argument("--output", type=Path, help="Write JSON here instead of stdout; must differ from input")
    args = parser.parse_args()
    try:
        if args.output and (args.output.resolve() == args.document.resolve()
                            or (args.output.exists() and args.output.samefile(args.document))):
            raise ValueError("output must not overwrite the input document")
        with zipfile.ZipFile(args.document) as package:
            report = extract(package, args.paper_mm, args.margins_mm, args.tolerance_mm)
        result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result, end="")
    except (OSError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError, RuntimeError) as exc:
        print(f"Cannot inspect DOCX: {exc}", file=sys.stderr)
        return 2
    return 0 if report["geometry_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
