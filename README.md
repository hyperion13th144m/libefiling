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
 - XMLファイルの文字コード変換
 - manifest.json の生成
 - いまのところ 特許願(A163) だけが処理対象。

## 動作環境
 - ubuntu bookworm
 - python 3.14

### 必要アプリのインストール
```bash
apt-get update
apt-get install -y python3.14
```

### libefiling パッケージのインストール
```bash
pip install libefiling
```

## 使い方
```python
from libefiling import parse_archive, Source

SRC = "202501010000123456_A163_____XXXXXXXXXX__99999999999_____AAA.JWX"
PROC = "202501010000123456_A163_____XXXXXXXXXX__99999999999_____AFM.XML"
OUT = "output"

# src のハッシュ値や文書コードを生成して、処理するか判定する例
source = Source.create(SRC)
document_code = source.get_document_code()
if document_code not in ["A163", "A151"]:
    raise ValueError(f"Unsupported document code: {document_code}")
if source.sha256 == "...":
    print("Already processed")
else:
    parse_archive(SRC, PROC, OUT)
```
 - generate_sha256 はアーカイブの内容に応じたハッシュ値を生成し、再処理判定用に使える。
 - parse_archive は SRC, PROC を OUT に展開する。
 - source = Source.create(SRC) の source は、manifest.json の sources フィールドと同じ形式。parse_archive するまえに、source.sha256 を得られるということ。

#### 出力ファイル
 - manifest.json : 展開後のファイルの情報
 - raw/ : SRC に含まれてたファイルが展開されてる。
 - xml/ : raw/*.xml と PROC を文字コード変換した xml が保存されてる。


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

0.1.54
 - 画像リサイズをスレッド化した。
 
0.1.55
 - 画像リサイズのために cykooze_resizer を選択できるようにした。

0.1.56
 - 画像リサイズのために pillow-simd を選択できるようにした。

0.1.60
 - get_document_code 関数は、manifest.jsonだけでなく、アーカイブパス・手続ファイルを与えても文書コードを返すようにした。
 - manifest.json に 文書コードを含めた

0.2.0
 - manifest.json の documents フィールドを sources フィールドに変更した。
   - sources の子要素は配列でなく archive, procedure とした。
   - sources.document_code フィールドは、文書コードを表す
 - get_document_code 廃止，Source クラスの get_document_code で代替
 - get_doc_id, generate_sha256 関数廃止, Source クラスの sha256 で代替
 - xml/sources.xml をはき出すようにした. manifest.json の sources フィールドと同じ内容を表す。

0.2.1
 - xml/images-information.xml をはき出すようにした. manifest.json の images フィールドと同じ内容 + ocr テキストを含んだxml

0.3.0
 ** API互換性がなくなっています。
 - 画像変換、OCR、xml/sources.xml、xml/images-information.xml の出力を廃止した。
 - 出力は manifest.json, xml/, raw/ のみとした。
