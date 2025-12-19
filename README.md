# libefiling

## 概要
 libefiling は インターネット出願ソフトのアーカイブを扱う python パッケージです。
 - [インターネット出願ソフト](https://www.pcinfo.jpo.go.jp/site/): 日本国特許庁に特許など出願する際に使うアプリ
 - アーカイブ: インターネット出願ソフトの「データ出力」で保存されるようなJWX(JPC,JWX)を本パッケージではそう呼んでる。
 - データ出力でアーカイブと一緒に出力されるXMLを手続XMLと呼ぶことにする。

## 機能
 - アーカイブの展開 -> XML, 画像ファイルが得られる
 - 画像ファイルのフォーマット変換、サイズ変換
 - XMLファイルの変換
 - いまのところ 特許願(A163) だけが処理対象。

## 動作環境
 - ubuntu bookworm
 - python 3.14
 - saxon-he, tesseract

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
### 1. アーカイブの展開
```python
from libefiling.archive import extract

SRC='202501010000123456_A163_____XXXXXXXXXX__99999999999_____AAA.JWX'
OUT='extracted'
extract(SRC, OUT)
```
```bash
$ ls extracted
JPODOCXML01-appb.xml
JPODOCXML01-jpbibl.xml
JPOXMLDOC01-jpfolb-I000001.tif
...
```

### 2. アーカイブに含まれる画像をwebpなどに変換し、XMLを加工する。

```python
import sys
from libefiling import parse_archive

params=[
    {
        "width": 300,
        "height": 300,
        "suffix": "-thumbnail",
        "format": ".webp",
        "attributes": [{"key": "sizeTag", "value": "thumbnail"}],
    },
    {
        "width": 600,
        "height": 600,
        "suffix": "-middle",
        "format": ".webp",
        "attributes": [{"key": "sizeTag", "value": "middle"}],
    },
    {
        "width": 800,
        "height": 0,
        "suffix": "-large",
        "format": ".webp",
        "attributes": [{"key": "sizeTag", "value": "large"}],
    },
],
SRC='202501010000123456_A163_____XXXXXXXXXX__99999999999_____AAA.JWX'
PROC='202501010000123456_A163_____XXXXXXXXXX__99999999999_____AFM.XML'
OUT='output'
parse_archive(SRC, PROC, OUT, params)
```
parse_archive の第4引数に、画像変換のパラメータを渡せる。
OUT に↓のファイルが保存される。

#### 出力ファイル
 - document.xml: アーカイブ中のXMLと手続XMLなどをまとめたXML
 - document.json: アーカイブ中のXMLと手続XMLなどをまとめたjson. このjsonは、検索エンジンに食わせたり、htmlにレンダリングするなどの用途を想定している。
 - *.webp 画像ファイル 

```bash
$ cat document.xml
<root xmlns:jp="http://www.jpo.go.jp">
  <application-body country="JP" dtd-version="1.6" lang="ja" status="n">
    <description>
      <invention-title>処理システム</invention-title>
      <technical-field>
        <p num="0001">本発明は、システムに関する。</p>
      </technical-field>
      ...
    </description>
    <claims>
      <claim num="1">
        <claim-text>...</claim-text>
      </claim>
      <claim num="2">
        <claim-text>
        <claim-text>...</claim-text>
      </claim>
      ...
    </claims>
    <abstract>
      <p num="">【要約】...</p>
    </abstract>
    <drawings>
      <figure num="1">
        <img he="187.4" wi="170.0" file="JPOXMLDOC01-appb-D000001.tif" img-format="tif" />
      </figure>
      ...
    </drawings>
  </application-body>
  <pkgheader lang="ja" dtd-version="1.1">
    ...
  </pkgheader>
  <jp:filelist lang="ja" dtd-version="1.0">
    <jp:file-content file-name="JPOXMLDOC01-appb-D000001.tif" jp:file-type="tif" />
    ...
  </jp:filelist>
  <package-data lang="ja" dtd-version="1.3" produced-by="applicant" country="JP">
    ...
  </package-data>
  <images>
    <image orig="JPOXMLDOC01-appb-D000001.tif" new="JPOXMLDOC01-appb-D000001-thumbnail.webp" width="300" height="300" kind="figure" sizeTag="thumbnail" />
    <image orig="JPOXMLDOC01-appb-D000001.tif" new="JPOXMLDOC01-appb-D000001-middle.webp" width="600" height="600" kind="figure" sizeTag="middle" />
    <image orig="JPOXMLDOC01-appb-D000001.tif" new="JPOXMLDOC01-appb-D000001-large.webp" width="800" height="1007" kind="figure" sizeTag="large" />
    ...
  </images>
  <jp:pat-app-doc lang="ja" dtd-version="1.0">
    ...
  </jp:pat-app-doc>
  <procedure-params>
    <procedure-param name="document-name">特許願</procedure-param>
    ...
  </procedure-params>
</root>```

```bash
$ cat document.json
{

  "docId": "7899534215aa5902bb1b0ffdc9a421a0",
  "archive": "209901010000123456_A163_____XXXXXXXXXX__99999999999_____AAA.JWX",
  "ext": ".JWX",
  "kind": "AAA",
  "schemaVer": "1.0",
  "documentName": "特許願",
  "documentCode": "A163",
  "law": "patent",
  "fileReferenceID": "X9999",
  "registrationNumber": null,
  "applicationNumber": "2099499999",
  "internationalApplicationNumber": null,
  "appealReferenceNumber": null,
  "submissionDate": "20990509",
  "submissionTime": "151210",
  "receiptNumber": "91920999199",
  "textBlocksRoot": [
    {
      "tag": "applicationForm",
      "blocks": [
        {
          "tag": "document-code",
          "text": "A163",
          "jpTag": "【書類名】",
          "convertedText": "特許願",
          "indentLevel": "0"
        },
       ...
  ...
}
```

## 注意事項
 - テストは十分でないので、いろいろバグあるとおもう。
 - 本アプリで何らかの損害を被っても本アプリ作者は責任を負いません。

## ライセンス
MIT ライセンス

## Reference
特許庁 日本国特許庁電子文書交換標準仕様XML編 （抜粋版）
  https://www.jpo.go.jp/system/patent/gaiyo/sesaku/document/touroku_jyohou_kikan/shomen-entry-02jpo-shiyosho.pdf


## TODO
意見書、補正書、拒絶理由通知書あたりの対応
