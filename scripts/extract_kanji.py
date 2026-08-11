import argparse
import re

#
#
# python3.11 extract_kanji.py ruby.csv CW38.csv ruby_CW38.csv

KANJI_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]+")


def load_dictionary(path):
    dictionary = {}

    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            # タブでもスペースでも対応
            parts = re.split(r"\s+", line, maxsplit=1)

            if len(parts) < 2:
                continue

            word = parts[0].strip()
            yomi = parts[1].strip()

            if word.lower() == "kanji":
                continue

            if word and yomi:
                dictionary[word] = yomi

    return dictionary


def extract_words(text):
    """
    本文中の「連続した漢字」を、そのまま1語として抽出する。
    部分文字列は作らない。
    """
    return set(KANJI_RE.findall(text))


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("dictionary")
    parser.add_argument("input")
    parser.add_argument("output")

    args = parser.parse_args()

    dictionary = load_dictionary(args.dictionary)

    with open(args.input, "r", encoding="utf-8-sig") as f:
        text = f.read()

    words = extract_words(text)

    words = sorted(words)

    with open(args.output, "w", encoding="utf-8") as f:
        for word in words:
            yomi = dictionary.get(word, "")
            f.write(f"{word}\t{yomi}\n")

    matched = sum(
        1 for word in words
        if word in dictionary
    )

    print(f"漢字のまとまり: {len(words)}")
    print(f"読みあり      : {matched}")
    print(f"読みなし      : {len(words) - matched}")


if __name__ == "__main__":
    main()