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

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    main()