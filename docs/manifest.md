# manifest.json 仕様解説

本ドキュメントでは、libefiling が出力する `manifest.json` の構造と
設計意図について説明する。

`manifest.json` は、アーカイブから抽出・正規化された各種リソース
（XML・画像・OCR結果など）を **後段の処理系が一貫して扱うための
メタデータファイル**である。

---

## 1. manifest.json の目的

manifest.json の主な目的は以下のとおりである。

- 出力ディレクトリ内に存在するファイルを機械的に列挙する
- 後段の処理（XML統合、IR生成、HTML生成、検索インデックス作成）が
  **ディレクトリ構造に依存せず**処理できるようにする
- 再処理・差分判定のための追跡情報（ハッシュ等）を提供する

---

## 2. 設計方針

manifest.json は、次の設計方針に基づいている。

- libefiling は **解釈を最小限に留める**
- ファイルの意味づけ（統合・分類・IR化）は後段で行う
- 仕様変更や例外的な構造に耐える柔軟な構成とする

そのため、manifest.json には
「何が存在するか」は記載するが、
「それをどう使うか」は含めない。

---

## 3. 全体構造

```json
{
  "manifest_version": "1.0.0",
  "generator": { ... },
  "document": { ... },
  "paths": { ... },
  "xml_files": [ ... ],
  "images": [ ... ],
  "stats": { ... }
}
```

## 4. 各フィールドの説明
### 4.1 manifest_version
```json
"manifest_version": "1.0.0"
```

- manifest.json 自体のバージョン
- 後段処理はこの値を参照して互換性を判断する


## 4.2 generator
```json
"generator": {
  "name": "libefiling",
  "version": "0.1.0",
  "created_at": "2026-01-04T11:20:30+09:00"
}
```

- manifest.json を生成したツール情報
- 再現性やデバッグのために使用される


## 4.3 document
```json
"document": {
  "doc_id": "D000001",
  "source": {
    "archive_filename": "...AAA.JWX",
    "archive_sha256": "...",
    "byte_size": 12345678,
    "task": "A",
    "kind": "AA",
    "extension": ".JWX"
  },
  "procedure_source": {
      "procedure_filename": "...AFM.XML",
      "procedure_sha256": "...",
      "byte_size": 4220
  }
}
```

- doc_id は、この文書単位を一意に識別するためのID
- source はアーカイブファイルに関する情報
- archive_sha256 は再処理判定や追跡用
- task, kind, extension はファイル名から得られるアーカイブの属する業務、種類、拡張子
- procedure_source は手続き情報ファイルに関する情報

### 4.4 paths
```json
"paths": {
  "root": ".",
  "raw_dir": "raw",
  "xml_dir": "xml",
  "images_dir": "images",
  "ocr_dir": "ocr"
}
```

- 各リソースが配置されているディレクトリ名
- 相対パスとして解釈される
- 後段処理は これらの値のみを参照してファイルにアクセスする


### 4.5 xml_files
```json
"xml_files": [
  {
    "path": "xml/JPOXMLDOC01.xml",
    "original_path_in_archive": "JPOXMLDOC01.xml",
    "sha256": "...",
    "encoding": {
      "detected": "Shift_JIS",
      "normalized_to": "UTF-8",
      "had_bom": false
    },
    "role_hint": "unknown"
  }
]
```

- アーカイブに含まれていた XML ファイルの一覧
- libefiling は XML の役割（請求項、明細書等）を 確定しない
- role_hint は将来拡張用であり、初期状態では unknown とする

### 4.6 images
```json
"images": [
  {
    "id": "img-0001",
    "kind": "figure",
    "original": {
      "path": "raw/JPOIMG0001.tif",
      "sha256": "...",
      "media_type": "image/tiff"
    },
    "derived": [
      {
        "path": "images/JPOIMG0001-thumbnail.webp",
        "width": 300,
        "height": 300,
        "attributes": [
           {
                "key": "sizeTag",
                "value": "thumbnail"
           }
        ],
        "sha256": "..."
      }
    ],
    "ocr": {
      "enabled": true,
      "results": [
        {
          "path": "ocr/img-0001.txt",
          "sha256": "...",
          "lang": "jpn"
        }
      ]
    }
  }
]
```

- original は元の画像（主に TIF）
- derived は Web 表示用に生成された画像
- deribed 内の attributes は画像変換時の付加情報を格納する
- OCR 結果は画像単位で紐づけられる


### 4.7 stats
```json
"stats": {
  "xml_count": 3,
  "image_original_count": 12,
  "image_derived_count": 24,
  "ocr_result_count": 12
}
```

- 出力内容のサマリ情報
- ログや検証、簡易チェック用途
