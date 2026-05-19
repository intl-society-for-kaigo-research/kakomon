#!/bin/sh -e

# _P36.Rmd は、第36回の過去問です。
# 過去問のうち、音声読み上げ用試験問題 から作成しました。
# https://www.sssc.or.jp/kaigo/past_exam/index.html
# まず、ルビを変換します
# 次に、過去問サイト用にデータ化します。JSON 形式です。
# この段階では正答が設定されていないので、正答選択肢を correct に移します。
# 一つ上のフォルダに移動させます。

rm _*_ruby.Rmd *.json

./section.sh _P38.Rmd _P38_sec.Rmd
./ruby.sh _P38_sec.Rmd _P38_ruby.Rmd
python3.13 ./convert.py _P38_ruby.Rmd P38.json

./section.sh _SW_P38.Rmd _SW_P38_sec.Rmd
./section.sh _SW_P37.Rmd _SW_P37_sec.Rmd
./section.sh _SW_P36.Rmd _SW_P36_sec.Rmd

./ruby.sh _SW_P38.Rmd _SW_P38_ruby.Rmd && \
python3.13 ./convert.py _SW_P38_ruby.Rmd _SW_P38.json


./ruby.sh _P36.Rmd _P36_ruby.Rmd && \
python ./convert.py _P36_ruby.Rmd P36.json

./ruby.sh _P37.Rmd _P37_ruby.Rmd && \
python ./convert.py _P37_ruby.Rmd P37.json

./ruby.sh _P38.Rmd _P38_ruby.Rmd && \
python ./convert.py _P38_ruby.Rmd P38.json