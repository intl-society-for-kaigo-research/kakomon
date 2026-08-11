import re
import csv
from pathlib import Path


def extract_answers(lines):
    answers = {}
    mode = False

    for line in lines:
        line = line.strip()

        if line.startswith("## 解答一覧"):
            mode = True
            continue

        if mode:
            if not line:
                continue

            m = re.match(r"([0-9]+)\s+([1-5])", line)
            if m:
                ref = f"問題{m.group(1)}"
                answers[ref] = int(m.group(2))

    return answers


def parse(text: str):
    lines = text.splitlines()
    answers = extract_answers(lines)

    data = []
    category = None
    current = None

    question_lines = []
    choices = []
    mode = "idle"

    def flush():
        nonlocal current, question_lines, choices

        if current:
            current["question"] = "\n".join(question_lines).strip()

            ref = current["ref"]

            # choicesをコピー
            wrongs = choices.copy()

            if ref in answers:
                idx = answers[ref] - 1

                if 0 <= idx < len(choices):
                    current["correct"] = choices[idx]

                    # correctをwrongsから削除
                    del wrongs[idx]

            current["wrongs"] = wrongs

            data.append(current)

        current = None
        question_lines = []
        choices = []

    for line in lines:
        line = line.rstrip()

        # カテゴリ
        m = re.match(r"^##\s*(.+)", line)
        if m:
            category = m.group(1).strip()
            continue

        # 問題開始
        m = re.match(r"^問題\s*([0-9０-９]+)\s*(.*)", line)
        if m:
            flush()

            current = {
                "category": category,
                "question": "",
                "correct": "",
                "wrongs": [],
                "explanation": "",
                "ref": f"問題{m.group(1)}"
            }

            question_lines = []
            choices = []
            mode = "question"

            rest = m.group(2).strip()
            if rest:
                question_lines.append(rest)

            continue

        # 選択肢 1
        m = re.match(r"^\s*1\s+(.*)", line)
        if m and current:
            mode = "choices"
            choices.append(m.group(1).strip())
            continue

        # 選択肢 2～5
        m = re.match(r"^\s*([2-5])\s+(.*)", line)
        if m and current and mode == "choices":
            choices.append(m.group(2).strip())
            continue

        # 空行スキップ
        if not line.strip():
            continue

        # question
        if current and mode == "question":
            question_lines.append(line.strip())

    flush()

    return data


def save_csv(data, output_path):
    # CSVの列
    fieldnames = [
        "category",
        "ref",
        "question",
        "correct",
        "wrong1",
        "wrong2",
        "wrong3",
        "wrong4",
        "explanation",
    ]

    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for item in data:
            wrongs = item.get("wrongs", [])

            row = {
                "category": item.get("category", ""),
                "ref": item.get("ref", ""),
                "question": item.get("question", ""),
                "correct": item.get("correct", ""),
                "wrong1": wrongs[0] if len(wrongs) > 0 else "",
                "wrong2": wrongs[1] if len(wrongs) > 1 else "",
                "wrong3": wrongs[2] if len(wrongs) > 2 else "",
                "wrong4": wrongs[3] if len(wrongs) > 3 else "",
                "explanation": item.get("explanation", ""),
            }

            writer.writerow(row)


if __name__ == "__main__":
    import sys

    input_path = Path(sys.argv[1])

    output_path = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else input_path.with_suffix(".csv")
    )

    print("==== DEBUG START ====")
    print("File exists:", input_path.exists())
    print("File size:", input_path.stat().st_size)

    text = input_path.read_text(encoding="utf-8")

    lines = text.splitlines()
    print("Total lines:", len(lines))

    result = parse(text)

    save_csv(result, output_path)

    print(f"✔ saved: {output_path}")

