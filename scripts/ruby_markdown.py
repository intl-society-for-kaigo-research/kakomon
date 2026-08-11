import argparse
import re


# python3.11 ruby_markdown.py ruby_CW37.csv CW37.csv CW37_Ruby.csv

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

    # テキストを置換
    return pattern.sub(
        lambda m: (
            f"{m.group(0)}｛{ruby_dict[m.group(0)]}｝"
        ),
        text
    )


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


def remove_okurigana(text):
    """
    漢字＋送り仮名｛読み＋送り仮名｝
    の末尾で一致するひらがなを、両方から取り除く。

    例:
        関す｛かんす｝る
        ↓
        関｛かん｝する

        関わる｛かかわる｝
        ↓
        関｛かか｝わる
    """

    hiragana = r"\u3041-\u3096"

    pattern = re.compile(
        rf"([\u3400-\u4DBF\u4E00-\u9FFF]+[{hiragana}]*)"
        rf"｛([^｛｝]+)｝"
    )

    def replace(match):
        body = match.group(1)
        reading = match.group(2)

        # 本文側と読み側の末尾にある、
        # 共通するひらがなのまとまりを探す
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

        if not new_body or not new_reading:
            return match.group(0)

        return f"{new_body}｛{new_reading}｝{okurigana}"

    return pattern.sub(replace, text)


def main():
    parser = argparse.ArgumentParser(
        description="テキストに「漢字｛よみ｝」形式のルビを付ける"
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