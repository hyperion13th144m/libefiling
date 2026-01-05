# アーカイブ構造に関する補足資料

本ドキュメントは、日本特許庁の電子出願アーカイブの実データを解析することで確認された構造を整理したもの。

## 1. 公式情報
### 1.1　特許庁 日本国特許庁電子文書交換標準仕様XML編 
[特許庁 日本国特許庁電子文書交換標準仕様XML編 （抜粋版）](https://www.jpo.go.jp/system/patent/gaiyo/sesaku/document/touroku_jyohou_kikan/shomen-entry-02jpo-shiyosho.pdf)


 1-4 ページ「１．１．２　ファイル構成」を引用
> （１）出願人・代理人の方が出願時に送信するとき 
![file-1](./file-1.png)

>（２）出願人・代理人の方に発送するとき 

>①インターネットによる発送のとき 


![file-2](./file-2.png)

>   ②ＩＳＤＮによる発送のとき 

![file-3](./file-3.png)


### 1.2 電子出願ソフトサポートサイト Q&A
[ファイルの命名規約](https://www.pcinfo.jpo.go.jp/site/3_support/2_faq/pdf/09_09_file-name.pdf)

ファイル名の最後のほう AAA.JWX などになっている。
５７文字目（一文字）
 - A 出願系
 - N 発送系

５８－５９文字目（二文字）
 - AA 受理済
 - NF 発送書類

拡張子
 - JPA：特許庁送受信Xﾌｫｰﾏｯﾄﾌｧｲﾙ
 - JPB：特許庁送受信旧SGMLﾌｫｰﾏｯﾄﾌｧｲﾙ　←pkgheader無しSGML
 - JPC：特許庁送受信XMLﾌｫｰﾏｯﾄﾌｧｲﾙ ｲﾝﾀｰﾈｯﾄ出願ｿﾌﾄ緊急避難用送信XMLﾌｫｰﾏｯﾄﾌｧｲﾙ
 - JPD：特許庁送受信新SGMLﾌｫｰﾏｯﾄﾌｧｲﾙ　←pkgheader付きSGML ｲﾝﾀｰﾈｯﾄ出願ｿﾌﾄ緊急避難用送信SGMLﾌｫｰﾏｯﾄﾌｧｲﾙ
 - JWX：特許庁送受信電子署名付XMLﾌｧｲﾙﾌｫｰﾏｯﾄ
 - JWS：特許庁送受信電子署名付SGMLﾌｧｲﾙﾌｫｰﾏｯﾄ

## 2. 用語
- 「電子出願アーカイブ(単にアーカイブとも)」: 仕様「１．１．２ ファイル構成」の「ファイル」のこと
-  出願系アーカイブ:「１．１．２ ファイル構成の（１）のファイル」
-  発送系アーカイブ:「１．１．２ ファイル構成の（２）のファイル」

## 3. 前提・対象範囲

- 対象とするのは、日本特許庁の電子出願用アーカイブファイルである
- 将来の仕様変更により、本資料の内容が当てはまらなくなる可能性がある
### 3.1 対象のファイル
 - 出願系アーカイブ ↓のようなファイル名
   - *AAA.JWX
   - *AAA.JWS
   - *AAA.JPC
   - *AAA.JPD
 - 発送系アーカイブ ↓のようなファイル名
   - *NNF.JWX
   - *NNF.JWS
   - *NNF.JPC

拡張子 JPA, JPB はデータが無いのでわからない。

## 4. 実データから観測されたアーカイブ構造
実際の電子出願アーカイブを解析した結果、以下のような構造が観測された。

### 4.1 出願系
#### 4.1.1 基本構造
出願系アーカイブの16進ダンプは次のようである。
<table>
<tr>
 <th></th>
 <th>00</th>
 <th>01</th>
 <th>02</th>
 <th>03</th>
 <th>04</th>
 <th>05</th>
 <th>06</th>
 <th>07</th>
 <th>08</th>
 <th>09</th>
 <th>0A</th>
 <th>0B</th>
 <th>0C</th>
 <th>0D</th>
 <th>0E</th>
 <th>0F</th>
</tr>

<tr>
 <th>0000</th>
 <td colspan="6" style="color: black; background-color: yellow">magic number</td>
 <td colspan="4" style="color: white; background-color: green">Payload size</td>
 <td colspan="4" style="color: white; background-color: red">First part size</td>
 <td colspan="2" style="color: white; background-color: gray"></td>
</tr>

<tr>
 <th>0001</th>
 <td colspan="2" style="background-color: gray"></td>
 <td colspan="4" style="color: white; background-color: blue">Second part size</td>
 <td colspan="10" style="background-color: gray"></td>
</tr>

<tr>
    <th>0002</th>
    <td colspan="16" style="background-color: gray"></td>
</tr>

<tr>
    <th>0003</th>
    <td colspan="2" style="background-color: gray"></td>
    <td colspan="14" style="background-color: #AA0000">First Part</td>
</tr>
<tr>
    <th>0004</th>
    <td colspan="16" style="background-color: #AA0000"></td>
</tr>
<tr>
    <th>0005</th>
    <td colspan="8" style="background-color: #AA0000"></td>
    <td colspan="8" style="background-color: #0000AA">Second Part</td>
</tr>
<tr>
    <th>0006</th>
    <td colspan="16" style="background-color: #0000AA"></td>
</tr>
<tr>
    <th>0007</th>
    <td colspan="16" style="background-color: #0000AA"></td>
</tr>

<tr>
    <th>...</th>
    <td colspan="16" style="background-color: #0000AA"></td>
</tr>
<tr>
    <th>EOF<th>
    <td colspan="16"></td>
</tr>
</table>

- ファイルの先頭から 0x32バイトは固定長のヘッダ
- ヘッダのあとに FirstPartが続く
- First Part の後に Second Part が続く。
- アーカイブ全体のファイルサイズ = 先頭の magic number の 6 bytes + Payload Size （4bytes (unsigned?) integer)
- First Part のサイズ: ヘッダの First Part Size（4bytes (unsigned?) integer)
- Second Part のサイズ: ヘッダの Second Part Size（4bytes (unsigned?) integer)

magic number, First part, Second part は、拡張子毎にことなる
magic number は外れてるかもしれん

#### 4.1.2 AAA.JWX
- magic number: 49-31-32-30-31-30
- First Part: ZIP 形式
- Second Part: ZIPを含む WAD 形式

AAA.JWXは、 「1．1．2 ファイル構成 (1)のアーカイブ」に該当し、
そのFirst Part は　ZIP, Second Part は WADのことだとおもう。

#### 4.1.3 AAA.JWS
- magic number: 49-31-33-30-31-30
- First Part: ZIP 形式
- Second Part: MIME を含む WAD 形式

AAA.JWSは 「1．1．2 ファイル構成 (1)のアーカイブ」に似ているが、WAD内がZIPではなくMIME（multipart mime）である。

#### 4.1.4 AAA.JPC
- magic number: 30-31-32-30-31-30
- First Part: ZIP 形式
- Second Part: ZIP 形式

AAA.JPCは 「1．1．2 ファイル構成 (1)のアーカイブ」に似ているが、WADではなくZIPである。

#### 4.1.5 AAA.JPD
- magic number: 30-31-33-30-31-30
- First Part: ZIP 形式
- Second Part: MIME 形式

AAA.JPDは 「1．1．2 ファイル構成 (1)のアーカイブ」に似ているが、WADではなくMIME（multipart mime）である。

### 4.2 発送系
#### 4.2.1 基本構造
発送系アーカイブの16進ダンプは次のようである。
<table>
<tr>
 <th></th>
 <th>00</th>
 <th>01</th>
 <th>02</th>
 <th>03</th>
 <th>04</th>
 <th>05</th>
 <th>06</th>
 <th>07</th>
 <th>08</th>
 <th>09</th>
 <th>0A</th>
 <th>0B</th>
 <th>0C</th>
 <th>0D</th>
 <th>0E</th>
 <th>0F</th>
</tr>

<tr>
 <th>0000</th>
 <td colspan="6" style="color: black; background-color: yellow">magic number</td>
 <td colspan="4" style="color: white; background-color: green">Payload size</td>
 <td colspan="4" style="color: white; background-color: gray">Padding Part Size</td>
 <td colspan="2" style="color: white; background-color: red">First</td>
</tr>
 
<tr>
 <th>0001</th>
 <td colspan="2" style="color: white; background-color: red"> part size</td>
 <td colspan="4" style="color: white; background-color: blue">Second part size</td>
 <td colspan="10" style="background-color: gray">PaddingPart</td>
</tr>

<tr>
    <th>0002</th>
    <td colspan="16" style="background-color: gray"></td>
</tr>

<tr>
    <th>0003</th>
    <td colspan="16" style="background-color: #AA0000">First Part</td>
</tr>
<tr>
    <th>0004</th>
    <td colspan="16" style="background-color: #AA0000"></td>
</tr>
<tr>
    <th>0005</th>
    <td colspan="8" style="background-color: #AA0000"></td>
    <td colspan="8" style="background-color: #0000AA">Second Part</td>
</tr>
<tr>
    <th>0006</th>
    <td colspan="16" style="background-color: #0000AA"></td>
</tr>
<tr>
    <th>0007</th>
    <td colspan="16" style="background-color: #0000AA"></td>
</tr>

<tr>
    <th>...</th>
    <td colspan="16" style="background-color: #0000AA"></td>
</tr>
<tr>
    <th>EOF<th>
    <td colspan="16"></td>
</tr>
</table>

- ファイルの先頭から 0x16 バイトは固定長のヘッダ
- ヘッダのあとに なにか(Padding Part)がある
- First part はヘッダーサイズ(0x16) + Padding Part Size から始まる
- Second Part は ヘッダーサイズ(0x16) + Padding Part Size + First Part Size から始まる。
- アーカイブ全体のファイルサイズ = 先頭の magic number の 6 bytes + Payload Size （4bytes (unsigned?) integer)
- First Part のサイズ: ヘッダの First Part Size（4bytes (unsigned?) integer)
- Second Part のサイズ: ヘッダの Second Part Size（4bytes (unsigned?) integer)

#### 4.2.2 NNF.JWX
- magic number: 49-32-32-30-32-30
- First Part: ZIP 形式
- Second Part: ZIPを含むWAD形式

NNF.JWXは、 「1．1．2 ファイル構成 (2)①のアーカイブ」に該当し、
そのFirst Part は　ZIP, Second Part は WADのことだとおもう。

#### 4.2.3 NNF.JWS
- magic number: 49-32-31-30-32-30
- First Part: ZIP 形式
- Second Part: MIME を含む WAD 形式

#### 4.2.4 NNF.JPC
- magic number: 30-32-32-30-32-30
- First Part: ZIP 形式
- Second Part: なし

NNF.JPCは 「1．1．2 ファイル構成 (2)②のアーカイブ」に該当し、
First Partは そのアーカイブのZIPに該当すると思う。

### 4.3 WAD 形式
WAD 形式は、 Wrapped Application Documents の略だそうだ。ASN.1 フォーマットのデータである。
WADに含まれる ZIP や MIME を取得するためには、PKCS#7 SignedData - PKCS#7 Data を抜き出せばよさそう。oid を指定して抜き出せる。

  dot notation:
　1.2.840.113549.1.7.1

  ASN.1 notation:
  {iso(1) member-body(2) us(840) rsadsi(113549) pkcs(1) pkcs-7(7) id-data(1)}

抜き出したデータは、ZIPかmultipart mimeなので、そこからファイルを得られる。

## 5. 既知の例外・注意点
- WAD の oid は、仕様書で明記されていない。なのでそれ以外のoidを使ったファイルがあったら、うまくZIPやMIMEを取り出せない可能性がある。4-500件ぐらいを対象にしたところ、いまのところそのoidで抜け出しできている。
- magic number からAAA.JWXなどの種別を判定できるとおもうが、定かでないので、ファイル名から決定するほうがいいかも。
- multipart mime からファイルを抜き出そうとしたら、multipart mimeに含まれてはいけない文字が含まれていたことがあった。multipart mime の処理系のせいなのか、元のmimeデータの問題なのかわからない。

## 6. 将来の仕様変更に対する考え方

- バグや要望があれば Issue または Pull Request により対応する（あんまりGithubの使い方詳しくないけど）
-
## 7. 本ドキュメントの位置づけ

本ドキュメントは、公式仕様書の代替ではなく、libefiling の実装背景を補足する資料である。
