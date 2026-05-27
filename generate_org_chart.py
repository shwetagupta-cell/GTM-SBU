#!/usr/bin/env python3
import datetime as dt
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


SOURCE_PATH = Path("/Users/shwetagupta/Downloads/SME Manpower - Feb 2026.xlsx")
OUTPUT_PATH = Path("/Users/shwetagupta/Documents/New project/SME Org Chart - Feb 2026.xlsx")

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

TITLE_PATTERNS: List[Tuple[int, str, re.Pattern[str]]] = [
    (0, "founder", re.compile(r"\b(founder|chief executive officer|ceo)\b")),
    (1, "president", re.compile(r"(?<!vice )\bpresident\b")),
    (2, "senior vice president", re.compile(r"\b(senior vice president|svp)\b")),
    (3, "vice president", re.compile(r"(?<!assistant )(?<!senior )\b(vice president|vp)\b")),
    (4, "assistant vice president", re.compile(r"\b(assistant vice president|avp)\b")),
    (5, "head", re.compile(r"\bhead\b")),
    (6, "general manager", re.compile(r"(?<!assistant )(?<!deputy )\b(general manager|gm)\b")),
    (7, "deputy general manager", re.compile(r"\b(deputy general manager|dgm)\b")),
    (8, "assistant general manager", re.compile(r"\b(assistant general manager|agm)\b")),
    (9, "senior manager", re.compile(r"\bsenior manager\b")),
    (10, "manager", re.compile(r"(?<!assistant )(?<!senior )(?<!project )\bmanager\b")),
    (11, "assistant manager", re.compile(r"\bassistant manager\b")),
    (12, "senior project manager", re.compile(r"\bsenior project manager\b")),
    (13, "project manager", re.compile(r"(?<!assistant )(?<!senior )\bproject manager\b")),
    (14, "assistant project manager", re.compile(r"\bassistant project manager\b")),
    (15, "lead", re.compile(r"\blead\b")),
    (16, "senior executive", re.compile(r"\bsenior executive\b")),
    (17, "executive", re.compile(r"(?<!senior )\bexecutive\b")),
    (18, "senior", re.compile(r"\bsenior\b")),
]

KEYWORDS_FOR_AMBIGUITY = ("gm", "general manager", "dgm", "deputy general manager", "agm", "assistant general manager", "manager", "project manager")


@dataclass(frozen=True)
class Employee:
    row_num: int
    emp_code: str
    name: str
    designation: str
    grade: str
    location: str
    bu: str
    function: str
    department: str
    original_bu: str
    original_function: str
    title_rank: int
    grade_rank: int
    title_match: str
    ambiguity_reason: str


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def pick_first(*values: str) -> str:
    for value in values:
        normalized = normalize_whitespace(value)
        if normalized:
            return normalized
    return ""


def title_rank(designation: str) -> Tuple[int, str, str]:
    text = normalize_key(designation)
    hits: List[Tuple[int, str]] = []
    for rank, label, pattern in TITLE_PATTERNS:
        if pattern.search(text):
            hits.append((rank, label))
    if not hits:
        return (19, "", "base_role")
    hits.sort(key=lambda item: item[0])
    best_rank, best_pattern = hits[0]
    unique_ranks = sorted({rank for rank, _ in hits})
    reason = ""
    if len(unique_ranks) > 1 and any(keyword in text for keyword in KEYWORDS_FOR_AMBIGUITY):
        reason = "ambiguous title keywords"
    return (best_rank, best_pattern, reason)


def grade_rank(grade: str) -> int:
    match = re.fullmatch(r"([A-Za-z]+)\s*(\d+)", normalize_whitespace(grade))
    if not match:
        return 999
    prefix, number = match.groups()
    prefix_score = {"g": 0, "f": 100, "e": 200}.get(prefix.lower(), 500)
    return prefix_score + int(number)


def excel_serial_to_date(value: str) -> str:
    try:
        serial = float(value)
    except (TypeError, ValueError):
        return normalize_whitespace(value)
    base = dt.datetime(1899, 12, 30)
    return (base + dt.timedelta(days=serial)).strftime("%Y-%m-%d")


def read_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values = []
    for si in root.findall("a:si", NS):
        values.append("".join(t.text or "" for t in si.iterfind(".//a:t", NS)))
    return values


def iter_sheet_rows(zf: zipfile.ZipFile, sheet_path: str) -> Iterable[Dict[str, str]]:
    shared = read_shared_strings(zf)
    root = ET.fromstring(zf.read(sheet_path))
    for row in root.findall(".//a:sheetData/a:row", NS):
        current: Dict[str, str] = {}
        for cell in row.findall("a:c", NS):
            ref = cell.attrib.get("r", "")
            col = "".join(ch for ch in ref if ch.isalpha())
            inline = cell.find("a:is", NS)
            value_node = cell.find("a:v", NS)
            if inline is not None:
                value = "".join(node.text or "" for node in inline.iterfind(".//a:t", NS))
            elif value_node is None:
                value = ""
            else:
                raw = value_node.text or ""
                if cell.attrib.get("t") == "s" and raw.isdigit():
                    index = int(raw)
                    value = shared[index] if index < len(shared) else raw
                else:
                    value = raw
            current[col] = value
        yield current


def load_employees(source: Path) -> Tuple[List[Employee], List[List[str]], Counter]:
    employees: List[Employee] = []
    issues: List[List[str]] = []
    counts: Counter = Counter()
    with zipfile.ZipFile(source) as zf:
        rows = list(iter_sheet_rows(zf, "xl/worksheets/sheet1.xml"))
    if not rows:
        raise RuntimeError("SME sheet is empty")
    headers = rows[0]
    for index, row in enumerate(rows[1:], start=2):
        row_values = {headers.get(col, col): normalize_whitespace(value) for col, value in row.items()}
        if not any(row_values.values()):
            continue
        category = row_values.get("Category", "")
        if category != "Current":
            counts["excluded_non_current"] += 1
            continue
        name = row_values.get("Employee Name", "")
        designation = row_values.get("Actual Designation", "")
        grade = row_values.get("Grade", "")
        bu = pick_first(row_values.get("Split into", ""), row_values.get("Master BU 2", ""), row_values.get("Sub New Business Unit", ""))
        function = pick_first(row_values.get("Department 2", ""), row_values.get("Department", ""))
        if not all((name, designation, bu, function)):
            issues.append([
                str(index),
                row_values.get("Emp Code", ""),
                name,
                designation,
                grade,
                bu,
                function,
                "missing core identity fields",
            ])
            counts["excluded_missing_core"] += 1
            continue
        t_rank, matched_pattern, ambiguity_reason = title_rank(designation)
        employee = Employee(
            row_num=index,
            emp_code=row_values.get("Emp Code", ""),
            name=name,
            designation=designation,
            grade=grade,
            location=row_values.get("Location", ""),
            bu=bu,
            function=function,
            department=row_values.get("Department", ""),
            original_bu=row_values.get("Split into", "") or row_values.get("Master BU 2", "") or row_values.get("Sub New Business Unit", ""),
            original_function=row_values.get("Department 2", "") or row_values.get("Department", ""),
            title_rank=t_rank,
            grade_rank=grade_rank(grade),
            title_match=matched_pattern,
            ambiguity_reason=ambiguity_reason,
        )
        employees.append(employee)
        counts["included_current"] += 1
    return employees, issues, counts


def seniority_sort_key(employee: Employee) -> Tuple[int, int, str, str]:
    return (employee.title_rank, employee.grade_rank, normalize_key(employee.designation), normalize_key(employee.name))


def choose_parent(candidates: List[Employee], employee: Employee) -> Tuple[Optional[Employee], Optional[str]]:
    eligible: List[Employee] = []
    for candidate in candidates:
        if candidate.name == employee.name and candidate.emp_code == employee.emp_code:
            continue
        if candidate.title_rank < employee.title_rank:
            eligible.append(candidate)
            continue
        if candidate.title_rank == employee.title_rank and candidate.grade_rank < employee.grade_rank:
            eligible.append(candidate)
    if not eligible:
        return (None, "orphan root")
    eligible.sort(key=seniority_sort_key)
    parent = eligible[-1]
    same_score = [
        item for item in eligible
        if item.title_rank == parent.title_rank and item.grade_rank == parent.grade_rank
    ]
    if len(same_score) > 1:
        return (parent, "ambiguous seniority")
    return (parent, employee.ambiguity_reason or None)


def build_org_chart(employees: List[Employee], issues: List[List[str]]) -> Tuple[List[List[str]], List[List[str]], Counter]:
    partitions: Dict[Tuple[str, str], List[Employee]] = defaultdict(list)
    for employee in employees:
        partitions[(employee.bu, employee.function)].append(employee)

    parent_map: Dict[Tuple[str, str], Optional[Employee]] = {}
    reason_map: Dict[Tuple[str, str], Optional[str]] = {}
    children: Dict[Tuple[str, str], List[Employee]] = defaultdict(list)
    root_counts: Counter = Counter()
    summary_counts: Counter = Counter()

    for partition_key, members in partitions.items():
        sorted_members = sorted(members, key=seniority_sort_key)
        for employee in sorted_members:
            parent, reason = choose_parent(sorted_members, employee)
            identity = (employee.emp_code, employee.name)
            parent_map[identity] = parent
            reason_map[identity] = reason
            summary_counts[partition_key] += 1
            if parent is None:
                root_counts[partition_key] += 1
            else:
                children[(parent.emp_code, parent.name)].append(employee)

    org_rows: List[List[str]] = []

    def traverse(employee: Employee, level: int) -> None:
        identity = (employee.emp_code, employee.name)
        parent = parent_map[identity]
        org_rows.append([
            str(level),
            parent.name if parent else "",
            employee.name,
            employee.designation,
            employee.grade,
            employee.bu,
            employee.function,
            employee.location,
            employee.emp_code,
            str(employee.row_num),
        ])
        for child in sorted(children.get(identity, []), key=seniority_sort_key):
            traverse(child, level + 1)

    roots = [
        employee for employee in employees
        if parent_map[(employee.emp_code, employee.name)] is None
    ]
    for root in sorted(roots, key=lambda employee: (normalize_key(employee.bu), normalize_key(employee.function), *seniority_sort_key(employee))):
        traverse(root, 0)

    seen = set()
    for row in org_rows:
        seen.add((row[8], row[2]))
    for employee in employees:
        identity = (employee.emp_code, employee.name)
        reason = reason_map[identity]
        if reason:
            issues.append([
                str(employee.row_num),
                employee.emp_code,
                employee.name,
                employee.designation,
                employee.grade,
                employee.bu,
                employee.function,
                reason,
            ])

    summary_rows: List[List[str]] = [["BU", "Function", "Employee Count", "Root Count"]]
    for (bu, function), count in sorted(summary_counts.items(), key=lambda item: (normalize_key(item[0][0]), normalize_key(item[0][1]))):
        summary_rows.append([bu, function, str(count), str(root_counts[(bu, function)])])
    summary_rows.append([])
    summary_rows.append(["Metric", "Value"])
    summary_rows.extend([
        ["Included Current Employees", str(len(employees))],
        ["Org Chart Rows", str(len(org_rows))],
        ["Unique Roots", str(sum(root_counts.values()))],
        ["Issue Rows", str(len(issues))],
    ])

    issues_with_header = [["Source Row", "Emp Code", "Employee Name", "Designation", "Grade", "BU", "Function", "Reason"]]
    issues_with_header.extend(issues)
    return org_rows, issues_with_header, summary_rows


def excel_column_name(index: int) -> str:
    name = ""
    while index >= 0:
        index, rem = divmod(index, 26)
        name = chr(ord("A") + rem) + name
        index -= 1
    return name


def make_shared_strings(sheets: List[List[List[str]]]) -> Tuple[List[str], Dict[str, int]]:
    lookup: Dict[str, int] = {}
    ordered: List[str] = []
    for sheet in sheets:
        for row in sheet:
            for value in row:
                if value == "":
                    continue
                if value not in lookup:
                    lookup[value] = len(ordered)
                    ordered.append(value)
    return ordered, lookup


def write_sheet_xml(rows: List[List[str]], string_lookup: Dict[str, int]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        '  <sheetData>',
    ]
    for row_idx, row in enumerate(rows, start=1):
        lines.append(f'    <row r="{row_idx}">')
        for col_idx, value in enumerate(row):
            if value == "":
                continue
            cell_ref = f"{excel_column_name(col_idx)}{row_idx}"
            if re.fullmatch(r"-?\d+(\.\d+)?", value):
                lines.append(f'      <c r="{cell_ref}"><v>{escape(value)}</v></c>')
            else:
                shared_index = string_lookup[value]
                lines.append(f'      <c r="{cell_ref}" t="s"><v>{shared_index}</v></c>')
        lines.append("    </row>")
    lines.extend([
        "  </sheetData>",
        "</worksheet>",
    ])
    return "\n".join(lines)


def write_workbook(output: Path, org_rows: List[List[str]], issues_rows: List[List[str]], summary_rows: List[List[str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    org_sheet = [[
        "Level",
        "Parent Name",
        "Employee Name",
        "Designation",
        "Grade",
        "BU",
        "Function",
        "Location",
        "Emp Code",
        "Source Row",
    ]] + org_rows
    sheets = [org_sheet, issues_rows, summary_rows]
    shared_strings, lookup = make_shared_strings(sheets)
    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Org Chart" sheetId="1" r:id="rId1"/>
    <sheet name="Org Chart Issues" sheetId="2" r:id="rId2"/>
    <sheet name="Summary" sheetId="3" r:id="rId3"/>
  </sheets>
</workbook>
"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>
"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>
"""
    shared_xml_lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">',
    ]
    for item in shared_strings:
        shared_xml_lines.append(f"  <si><t>{escape(item)}</t></si>")
    shared_xml_lines.append("</sst>")
    shared_xml = "\n".join(shared_xml_lines)

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/sharedStrings.xml", shared_xml)
        zf.writestr("xl/worksheets/sheet1.xml", write_sheet_xml(org_sheet, lookup))
        zf.writestr("xl/worksheets/sheet2.xml", write_sheet_xml(issues_rows, lookup))
        zf.writestr("xl/worksheets/sheet3.xml", write_sheet_xml(summary_rows, lookup))


def main() -> None:
    employees, issues, counts = load_employees(SOURCE_PATH)
    org_rows, issues_rows, summary_rows = build_org_chart(employees, issues)
    summary_rows.append([])
    summary_rows.append(["Source Filter Metric", "Count"])
    for key in ("included_current", "excluded_non_current", "excluded_missing_core"):
        summary_rows.append([key, str(counts.get(key, 0))])
    write_workbook(OUTPUT_PATH, org_rows, issues_rows, summary_rows)
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Included current employees: {counts.get('included_current', 0)}")
    print(f"Org chart rows: {len(org_rows)}")
    print(f"Issue rows: {len(issues_rows) - 1}")


if __name__ == "__main__":
    main()
