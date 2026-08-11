import re
import json
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
            current["question"] = "\\n".join(question_lines).strip()
    
            ref = current["ref"]
    
            # ★ choicesをコピー（元を壊さない）
            wrongs = choices.copy()
    
            if ref in answers:
                idx = answers[ref] - 1
                if 0 <= idx < len(choices):
                    current["correct"] = choices[idx]
    
                    # ★ correctをwrongsから削除
                    del wrongs[idx]
    
            current["wrongs"] = wrongs
    
            data.append(current)
    
        current = None
        question_lines = []
        choices = []

    for line in lines:
        line = line.rstrip()

        # カテゴリ（flushしない！！！）
        m = re.match(r"^##\s*(.+)", line)
        if m:
            category = m.group(1).strip()
            continue

        # 問題開始
        m = re.match(r"^問題\s*([0-9０-９]+)\s*(.*)", line)
        if m:
            flush()  # ←ここだけ

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

        # 選択肢開始
        m = re.match(r"^\s*1\s+(.*)", line)
        if m and current:
            mode = "choices"
            choices.append(m.group(1).strip())
            continue

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


if __name__ == "__main__":
    import sys
    from pathlib import Path
    import json

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".json")

    print("==== DEBUG START ====")
    print("File exists:", input_path.exists())
    print("File size:", input_path.stat().st_size)

    text = input_path.read_text(encoding="utf-8")

    lines = text.splitlines()
    print("Total lines:", len(lines))
        
    result = parse(text)

    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✔ saved: {output_path}")
