import argparse
import re
from pathlib import Path

# python3.11 merge_ruby.py ruby*.csv -o ruby_all.tsv

def load_tsv(path):
    data = {}

    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\r\n")

            if not line.strip():
                continue

            # タブ、またはスペース区切りにも対応
            parts = re.split(r"\s+", line.strip(), maxsplit=1)

            if not parts:
                continue

            word = parts[0].strip()

            if not word:
                continue

            yomi = ""
            if len(parts) >= 2:
                yomi = parts[1].strip()

            # 同じ単語があった場合
            if word not in data:
                data[word] = yomi
            elif not data[word] and yomi:
                # 空欄より読みありが優先
                data[word] = yomi

    return data


def main():
    parser = argparse.ArgumentParser(
        description="複数のruby TSVを一つにまとめる"
    )

    parser.add_argument(
        "inputs",
        nargs="+",
        help="入力TSVファイル"
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="出力TSVファイル"
    )

    args = parser.parse_args()

    merged = {}

    for filename in args.inputs:
        print(f"読み込み: {filename}")

        data = load_tsv(filename)

        for word, yomi in data.items():

            if word not in merged:
                merged[word] = yomi

            elif not merged[word] and yomi:
                merged[word] = yomi

    # 単語順に並べる
    words = sorted(merged)

    with open(args.output, "w", encoding="utf-8") as f:
        for word in words:
            f.write(f"{word}\t{merged[word]}\n")

    print()
    print(f"入力ファイル数: {len(args.inputs)}")
    print(f"統合語数: {len(words)}")
    print(f"読みあり: {sum(bool(v) for v in merged.values())}")
    print(f"読みなし: {sum(not v for v in merged.values())}")
    print(f"出力: {args.output}")


if __name__ == "__main__":
    main()