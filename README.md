# RA-Machine-PyInterpreter
ランダムアクセスマシン(RAM)モデルに基づいて記述されたプログラムを実行するシミュレータ

　
## ランダムアクセスマシン
**無限のメモリ**と**等しい命令コスト**( $\mathcal{O}(1)$ )を持つ計算機モデル。  
入力用テープ，出力用テープ，メモリ，プロセッサで構成される。  

### 入力用テープ
プログラムへの入力値(整数)がシーケンシャルに記録されたRead-Onlyなテープ。ランダムアクセスはできず，先頭から逐次読み込むのみである。

### 出力用テープ
プログラムからの出力値(整数)がシーケンシャルに記録されるWrite-Onlyなテープ。本プログラムではコンソール上の出力される。

### メモリ
番地は*r0*，*r1*，*r2*…と記述され，整数値が格納される。  
*r0*は演算専用のアキュムレータである。何らかの演算を行う際は，**LOAD**命令で対象の値を*r0*に読み出す必要がある。

### 参考文献
> https://www.geeksforgeeks.org/what-is-random-access-machine/

　
## 命令セットおよび記述方法
| 命令 | 説明 | 例 |
| ---- | ---- | ---- |
| LOAD | パラメータに指定されたアドレスから*r0*にデータをコピーする | LOAD 1 |
| STORE | *r0*からパラメータに指定されたアドレスにデータをコピーする | STORE 1 |
| ADD | *r0*にパラメータで指定されたアドレスの値を加算する | ADD 1 |
| SUB | *r0*にパラメータで指定されたアドレスの値を減算する | SUB 1 |
| MULT | *r0*にパラメータで指定されたアドレスの値を乗算する | MULT 1 |
| DIV | *r0*にパラメータで指定されたアドレスの値を除算する | DIV 1 |
| JUMP | パラメータで指定されたラベルにジャンプする | JUMP loop |
| JZERO | *r0*が0のとき，パラメータで指定されたラベルにジャンプする | JZERO loop |
| JGTZ | *r0*が1以上のとき，パラメータで指定されたラベルにジャンプする | JGTZ loop |
| READ | テープからパラメータに指定されたアドレスにデータを読み込む | READ 1 |
| WRITE | パラメータに指定されたアドレスのデータを出力する | READ 1 |
| HALT | プログラムを終了する | HALT |

### ラベル
ラベルを指定する際は，ジャンプ先の行の先頭にラベル名を指定し，末尾にセミコロン`:`をつける。  
ラベル名に使用できる文字は，半角英数字(大文字，小文字)，アンダーバー`_`およびハイフン`-`である。  
例: `loop_1:`　

### 間接アドレス指定
`LOAD`，`STORE`，`ADD`，`SUB`，`MULT`，`DIV`，`READ`，`WRITE`命令は，パラメータ指定時にアドレスの前に`*`を付加することで間接アドレスを指定できる。  
C言語でいうところのポインタと同等である。  
例: `LOAD *1` (*r1*に格納されているアドレスに格納されているデータを*r0*にコピーする)

### 即値
`LOAD`，`ADD`，`SUB`，`MULT`，`DIV`，`WRITE`命令は，パラメータ指定時に数値の前に`=`を付加することで即値を指定できる。  
例: `LOAD =1` (*r0*に1を格納する。)

### コメントアウト
`;`以降に記述された文字はコメントとなる。

### 例
`r1`を0で初期化する例を以下に示す
```
LOAD =0 ;即値0をr0に格納
STORE 1 ;r0の値をr1に格納(この場合は0)
```

`r1`に10がセットされている状態で，その値に5を加算して出力する例を以下に示す
```
LOAD 1  ;r0 ← r1 (10)
ADD =5  ;r0 ← r0 + 5 (15)
STORE 1 ;r1 ← r0 (15)
WRITE 1 ;r1の値を出力
```

'r1'をポインタとして，'r2'から'r5'の値を出力する例を以下に示す
```
LOAD =2   ;r2から出力するので即値2
STORE 1   ;r1 ← r0 (2)
loop:
WRITE *1  ;r1の指すアドレスの値を出力
LOAD 1    ;r1をr0にロード
ADD =1    ;r0をインクリメント
STORE 1   ;r0をr1にコピー
SUB =5    ;r0から5を引く(条件分岐のため)
JGTZ end  ;r0が1以上であれば，r5まで出力が終わっているのでラベルendにジャンプ
JUMP loop ;それ以外であればラベルloopにジャンプ
end:
HALT
```

　
## 実行方法
### Windows
```
python main.py <RAMファイル名>
```

### MacOS，Linux
```
python3 main.py <RAMファイル名>
```
**注意！　RAMファイルはUTF-8かShift-JISでエンコーディングする必要がある**

### コマンドライン引数
| 引数 | 説明 | 例 |
| ---- | ---- | ---- |
| -d | デバッグモードを有効にする。実行時の詳細がすべて出力されるため，プラグラムのデバッグ中は推奨 | -d |
| -t | 入力テープファイル名を指定する | -t <入力テープファイル名> |

　
## サンプルファイル実行方法
### 選択ソート
```
python3 main.py sample/selection_sort.ram -t sample/selection_sort.tape
```
