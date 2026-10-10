# Chapter 02: Raw File I/O

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

partial read/write、EOF、EINTR、error union。

## 前章とのつながり

fdを持てたので、byte streamを最後まで転送します。

## 背景

要求長と返却長は別です。readの0は非空bufferでEOFを示し、writeの正の短い返却値は進捗です。

## OS内部では何が起きているか

kernelはfile offsetからデータをbufferへコピーし、実際の転送量だけoffsetを進めます。signalやpipe容量で要求全量に達しない場合があります。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`openat, read, write, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.posix.openat/read と std.os.linux.read/write/errno`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `posix.zig / os/linux.zig`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 2 read
man 2 write
man 2 open
man 2 close
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

CLI cat PATH と cp SOURCE DEST を実装する。空・binary・大きなファイルを処理する。

## 実装手順

1. main.zigへcat PATHというCLIを自分で定義する。引数を得るAPIもprocess sourceから探す。
2. 入力fileをopenし、固定長bufferを用意する。
3. readの0、正の短い結果、errorを分け、EOFまで繰り返す。
4. writeの進捗offsetを持ち、残量を全て転送する。
5. cp SOURCE DESTを追加し、create/truncateと同一file拒否の方針を決める。
6. bufferを1 byteへ縮小し、元データと出力をcmpで比較する。
7. pipeとsignalで短い転送・EINTRを観測し、wrapperがretryする箇所をsourceで確かめる。

## 実行

前章と同様に、自分でmain.zigを作成してください。まず単一fileで書きます。

```sh
touch main.zig
$EDITOR main.zig
zig run main.zig
```

$EDITORは事前に設定したeditor名です（例: nvim）。コンパイラエラーも教材の一部です。
型、error union、optional、integer cast、pointer、alignment、sliceの要求を読み、修正して再実行します。
引数がある課題は`zig run main.zig -- 引数`で渡します。

## 手動で確認

CLIは`cat PATH`と`cp SOURCE DEST`を自分で実装します。Zig CLIとプログラム引数の境界は`--`です。

```sh
printf 'hello\n' > input.txt
zig run main.zig -- cat input.txt
zig build-exe main.zig
./main cat input.txt > output.txt
cmp input.txt output.txt
./main cp input.txt copy.txt
cmp input.txt copy.txt
truncate -s 0 empty.txt
./main cat empty.txt
./main cat missing.txt
```

空・binary・大きな入力、既存destのtruncateも試します。missing pathは非zero終了するか確認します。
`dd if=/dev/urandom of=input.bin bs=4096 count=256`でbinary入力を用意し、同様にcmpします。

## 観察ポイント

1 byte bufferと64KiB bufferでsyscall回数を予想し比較する。pipeでも試す。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

普段は`zig run main.zig`、観察時は先にbinaryを生成します。

```sh
zig build-exe main.zig
strace -f -tt -T -o trace.log ./main cat input.txt
strace -f -c ./main cat input.txt
```

引数がある課題は`./main`の後に付けます。serverは別terminalでclientを接続し、終了後の集計を読みます。
`zig run`自体をtraceするとcompilerとlinkerのsyscallが混ざるため、学習対象binaryだけを観測します。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
program初期化と自分の処理の違いも調べます。[観察手順](../docs/debugging.md)。

## よくある失敗

buffer全体を書く／partial write後にoffsetを進めない／closeをEINTRで盲目的に再試行する。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `posix.zig / os/linux.zig`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

std.posix.readはINTRを内部でretryする。生linux.readではerrnoを自分でdecodeする。writeが0で残量がある場合の停止方針を決める。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

空・binary・大きなfileのcat/cpがcmpで一致する。missing pathと短い転送の扱いを説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

signalとpipeでEINTRを観察し、SA_RESTARTの影響を記録する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> fileとsocketは同じread/writeでも待ち方がどう変わりますか？
