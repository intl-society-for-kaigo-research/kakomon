import argparse
import re


# python3.11 ruby.py ruby_CW37.csv CW37.csv CW37_Ruby.csv

def load_ruby_dictionary(path):
    ruby_dict = {}

    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            # タブ、または2個以上の空白で分割
            parts = re.split(r"\t+| {2,}", line)

            if len(parts) < 2:
                continue

            kanji = parts[0].strip()
            yomi = parts[1].strip()

            # ヘッダー
            if kanji == "kanji" and yomi == "yomi":
                continue

            if kanji and yomi:
                ruby_dict[kanji] = yomi

    return ruby_dict


def add_ruby(text, ruby_dict):
    # 長い語を優先
    words = sorted(ruby_dict, key=len, reverse=True)

    # 辞書を正規表現にする
    pattern = re.compile(
        "|".join(re.escape(word) for word in words)
    )

    # 既存の ruby を含む部分
    ruby_pattern = re.compile(
        r"<ruby>.*?</ruby>",
        re.DOTALL
    )

    # テキストを「既存ruby」と「通常テキスト」に分割
    parts = []
    pos = 0

    for match in ruby_pattern.finditer(text):
        # ruby より前の通常テキスト
        if match.start() > pos:
            normal = text[pos:match.start()]
            normal = pattern.sub(
                lambda m: (
                    f"<ruby>{m.group(0)}"
                    f"<rt>{ruby_dict[m.group(0)]}</rt></ruby>"
                ),
                normal
            )
            parts.append(normal)

        # 既存の ruby はそのまま
        parts.append(match.group(0))
        pos = match.end()

    # 最後の通常テキスト
    if pos < len(text):
        normal = text[pos:]
        normal = pattern.sub(
            lambda m: (
                f"<ruby>{m.group(0)}"
                f"<rt>{ruby_dict[m.group(0)]}</rt></ruby>"
            ),
            normal
        )
        parts.append(normal)

    return "".join(parts)

def remove_okurigana(text):
    """
    <ruby>漢字かな<rt>読みかな</rt></ruby>
    の末尾にある一致したひらがなを ruby の外に出す。
    """

    hiragana = r"\u3041-\u3096"

    pattern = re.compile(
        rf"<ruby>(.*?)<rt>(.*?)</rt></ruby>",
        re.DOTALL
    )

    def replace(match):
        body = match.group(1)
        reading = match.group(2)

        # 本文側・読み側の末尾から、
        # 同じひらがなが一致する部分を探す
        i = 0

        while (
            i < len(body)
            and i < len(reading)
            and re.match(rf"[{hiragana}]", body[-(i + 1)])
            and body[-(i + 1)] == reading[-(i + 1)]
        ):
            i += 1

        if i == 0:
            return match.group(0)

        okurigana = body[-i:]
        new_body = body[:-i]
        new_reading = reading[:-i]

        # ruby の中身が空になる場合は元のまま
        if not new_body or not new_reading:
            return match.group(0)

        return (
            f"<ruby>{new_body}<rt>{new_reading}</rt></ruby>"
            f"{okurigana}"
        )

    return pattern.sub(replace, text)


def remove_manual_ruby(text):
    """
    漢字｛よみ｝形式の既存ルビを削除する。

    例:
        蠕動運動｛ぜんどううんどう｝
        ↓
        蠕動運動

        胃｛い｝から腸｛ちょう｝へ
        ↓
        胃から腸へ
    """

    pattern = r'([\u3400-\u4DBF\u4E00-\u9FFF]+)｛[^｛｝]*｝'

    return re.sub(pattern, r'\1', text)

def main():
    parser = argparse.ArgumentParser(
        description="テキストにHTMLルビを付ける"
    )

    parser.add_argument("ruby_csv")
    parser.add_argument("input")
    parser.add_argument("output")

    args = parser.parse_args()

    ruby_dict = load_ruby_dictionary(args.ruby_csv)

    with open(args.input, "r", encoding="utf-8-sig") as f:
        text = f.read()

    result = remove_manual_ruby(text)
    result = add_ruby(result, ruby_dict)
    result = remove_okurigana(result)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    main()