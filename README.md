# libefiling

This library targets electronic filing data provided by the Japan Patent Office (JPO).
Detailed documentation is written in Japanese, as the primary users are Japanese.

## 概要
 libefiling は インターネット出願ソフトのアーカイブを扱う python パッケージです。
 - [インターネット出願ソフト](https://www.pcinfo.jpo.go.jp/site/): 日本国特許庁に特許など出願する際に使うアプリ
 - アーカイブ: インターネット出願ソフトの「データ出力」で保存されるようなJWX(JPC,JWX)を本パッケージではそう呼んでる。
 - データ出力でアーカイブと一緒に出力されるXMLを手続XMLと呼ぶことにする。

## 機能
 - アーカイブの展開 -> XML, 画像ファイルが得られる
 - 画像ファイルのフォーマット変換、サイズ変換
 - XMLファイルの文字コード変換
 - いまのところ 特許願(A163) だけが処理対象。

## 動作環境
 - ubuntu bookworm
 - python 3.14
 - tesseract

### 必要アプリのインストール
```bash
apt-get update
apt-get install -y python3.14 tesseract-ocr tesseract-ocr-jpn
```

### libefiling パッケージのインストール
```bash
pip install libefiling
```

## 使い方
```python
from libefiling import parse_archive, ImageConvertParam, generate_sha256, get_document_code, get_doc_id

params = [
    ImageConvertParam(
        width=300,
        height=300,
        suffix="-thumbnail",
        format=".webp",
        attributes=[{"key": "sizeTag", "value": "thumbnail"}],
    ),
    ImageConvertParam(
        width=600,
        height=600,
        suffix="-middle",
        format=".webp",
        attributes=[{"key": "sizeTag", "value": "middle"}],
    ),
    ImageConvertParam(
        width=800,
        height=0,
        suffix="-large",
        format=".webp",
        attributes=[{"key": "sizeTag", "value": "large"}],
    ),
]

SRC='202501010000123456_A163_____XXXXXXXXXX__99999999999_____AAA.JWX'
PROC='202501010000123456_A163_____XXXXXXXXXX__99999999999_____AFM.XML'
OUT='output'

### ocr 処理対象イメージの種類. 以下から選択
### OCR_TARGET = Literal[
###     "chemical-formulas", "figures", "equations", "tables", "other-images", "ALL"
### ]
ocr_target = ["other-images"]
doc_id = generate_sha256(SRC)
if doc_id === '...':
    print("Already processed")
else:
    parse_archive(SRC, PROC, OUT, params, ocr_target)

print(get_document_code("output/manifest.json"))
print(get_doc_id("output/manifest.json"))
```
 - generate_sha256 はアーカイブの内容に応じたハッシュ値を生成し、再処理判定用に使える。
 - parse_archive は SRC,PROCを OUTに展開する。第4引数に、画像変換のパラメータを渡せる。
OUT に各種ファイルが展開される。第5引数はOCR処理対象の画像種別を選択する. 第6引数は並列オプション。
   - max_workers が None のとき: 従来どおりシリアル実行
   - max_workers が 1 のとき: シリアル実行
   - max_workers が 2 以上のとき: スレッド並列実行
   - max_workers が 0 のとき: CPU数ベースで自動設定
 - get_document_code は parse_archive で生成された manifest.json のパスを与えると、文書コード(e.g. A163)を返す。
 - get_doc_id は parse_archive で生成された manifest.json のパスを与えると、doc_id を返す。

#### 出力ファイル
 - manifest.json : 展開後のファイルの情報
 - raw/ : SRC に含まれてたファイルが展展されてる。
 - xml/ : raw/*.xml 、PROC を文字コード変換したxml, イメージ変換の対応を表したxml が保存されてる。
 - images/ : raw の画像ファイルがparamsに従って変換された画像が保存されてる。
 - ocr/ : raw の画像ファイルごとにOCR処理してえられたテキストが保存されてる。


## 注意事項
 - テストは十分でないので、いろいろバグあるとおもう。
 - 読み取り元のファイル(SRC,PROCに指定したファイル)や展開後のファイルは、どこかに送信されることはありません。ソースみてもらえば。
 - 本アプリで何らかの損害を被っても本アプリ作者は責任を負いません。

## ライセンス
MIT ライセンス

## Reference
特許庁 日本国特許庁電子文書交換標準仕様XML編 （抜粋版）
  https://www.jpo.go.jp/system/patent/gaiyo/sesaku/document/touroku_jyohou_kikan/shomen-entry-02jpo-shiyosho.pdf


## 変更履歴
0.1.40
 - manifest の形式変更
   - xml, image の path を filename にした。

0.1.49
 - manifest の形式変更
   - xml_files の kind を追加
 - get_document_code 関数を追加

0.1.51
 - get_doc_id 関数を追加
