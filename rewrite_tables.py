"""v2 fix: rewrite every table row in the filings as a self-describing sentence.

Why: flattened 10-K tables look like `Revenue | $ | 130,497 | $ | 60,922`. That row has no
company name, no year and no statement name, so semantic search can't match a question like
"what was NVIDIA's revenue in fiscal 2025" to it. This turns it into:

  NVIDIA fiscal 2025 10-K, Consolidated Statements of Income (In millions, except per share data).
  Revenue: fiscal year ended Jan 26, 2025: $130,497 million; fiscal year ended Jan 28, 2024: ...

Writes two files per company, which are what gets uploaded:
  filings/<tag>_10k_<period>_tables.txt  one table row per paragraph, as a sentence
  filings/<tag>_10k_<period>_prose.txt   the 10-K with raw table rows removed
"""
import pathlib
import re

from companies import COMPANIES, filing_path, prose_path, tables_path

DATE = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, (19|20)\d\d$")
YEAR = re.compile(r"^(19|20)\d\d$")
NUM = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$|^—%?$|^\*$")
SKIP_CONTEXT = re.compile(r"^(table of contents|year ended|\d+|.*form 10-k.*)$", re.I)


PARTIAL_DATE = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},$")
STATEMENT = re.compile(r"consolidated (statements?|balance sheets?)", re.I)


def is_header_cell(c):
    c = c.replace("\n", " ").strip()
    return bool(DATE.match(c) or YEAR.match(c) or PARTIAL_DATE.match(c)
                or re.match(r"^(19|20)\d\d \w", c) and PARTIAL_DATE.match(c.split(" ", 1)[1])
                or c.lower() in {"change", "$ change", "% change", "$", "%"})


def pretty_header(c):
    if DATE.match(c):
        return f"fiscal year ended {c}"
    if YEAR.match(c):
        return f"fiscal {c}"
    return c.lower()


def parse_values(cells):
    """['$', '130,497', '$', '60,922', '—', '%', '( 247 )'] -> ['$130,497', '$60,922', '—%', '(247)']"""
    vals, dollar = [], False
    for c in cells:
        c = re.sub(r"\(\s*", "(", re.sub(r"\s*\)", ")", c.strip()))
        if not c:
            continue
        if c == "$":
            dollar = True
            continue
        if c == "%" and vals:
            vals[-1] += "%"
            continue
        vals.append(c)
        dollar = False
    return vals


def rewrite(tag):
    c = COMPANIES[tag]
    doc_label = f"{c['name']} {c['label']}"
    lines = pathlib.Path(filing_path(tag)).read_text(encoding="utf-8").splitlines()

    out, context, sub, headers, prev_plain, statement, in_header = [], [], "", [], "", "", False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if "|" not in line:
            if YEAR.match(line) and in_header:  # last year of a header split across lines
                headers.append(line)
                continue
            if len(line) > 160:  # prose paragraph: any table and its headings are over
                headers, sub, statement, context = [], "", "", []
            elif STATEMENT.search(line) and len(line) < 90:
                statement, context, sub = line.title() if line.isupper() else line, [], ""
            elif not SKIP_CONTEXT.match(line) and not is_header_cell(line) and not line.endswith("."):
                context = (context + [line])[-2:]
                sub = ""
            prev_plain = line
            continue

        cells = [x.strip() for x in line.split("|")]
        nonempty = [x for x in cells if x]
        if any("million" in x.lower() for x in nonempty[1:]):
            context = (context + ["(In millions)"])[-2:]
        if nonempty and all(is_header_cell(x) for x in nonempty):
            if any(PARTIAL_DATE.match(x) or " " in x and YEAR.match(x.split(" ")[0]) for x in nonempty):
                years = re.findall(r"(?:19|20)\d\d", line)  # dates split across lines: keep the years
                headers = (headers + years) if in_header else years
            else:
                headers = [x for x in nonempty if DATE.match(x) or YEAR.match(x) or x.lower() == "change"]
            in_header = True
            continue
        in_header = False

        label = cells[0]
        if not label and prev_plain and len(prev_plain) < 80:  # label wrapped onto the previous line
            label = prev_plain
            if context and context[-1] == prev_plain:
                context = context[:-1]
        if not label or NUM.match(label):
            continue
        vals = [v for v in parse_values(cells[1:]) if NUM.match(v.lstrip("$"))]
        if not vals:
            sub = label.rstrip(":")
            continue

        if headers and len(vals) == len(headers):
            pairs = list(zip(headers, vals))
        else:
            dates = [h for h in headers if h.lower() != "change"]
            pairs = list(zip(dates, vals)) if dates else []
        millions = any("million" in x.lower() for x in context + [statement]) or bool(statement)

        def money(v, h=""):
            if not millions or v.endswith("%") or h.lower() == "change" or v in ("*", "—"):
                return v
            return f"${v} million"

        if not millions and not any(v.endswith("%") for v in vals):
            continue  # table of contents / exhibit index / cover page rows, not financial data
        if pairs:
            body = "; ".join(f"{pretty_header(h)}: {money(v, h)}" for h, v in pairs)
        else:
            body = ", ".join(money(v) for v in vals)
        where = ", ".join(([statement] if statement else []) + context)
        name = f"{sub} - {label}" if sub else label
        out.append(f"{doc_label}, {where} | {name}: {body}")

    prose = [ln for ln in lines if "|" not in ln]
    pathlib.Path(prose_path(tag)).write_text("\n".join(prose), encoding="utf-8")

    path = pathlib.Path(tables_path(tag))
    path.write_text(f"{doc_label}: financial tables rewritten as sentences\n\n" + "\n\n".join(out), encoding="utf-8")
    return path, out


if __name__ == "__main__":
    for tag in COMPANIES:
        path, out = rewrite(tag)
        print(f"{tag}: {len(out)} table rows -> {path}")
        for s in out:
            if "Revenue:" in s or "Total net sales:" in s:
                print("  e.g.", s[:220])
                break
