# Chapter 01: File Descriptor

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

プロセスとfd table、0/1/2、open/close/read/write。

## 前章とのつながり

開始章です。端末とファイルを同じ整数で扱える理由を考えます。

## 背景

fdはプロセス内の索引です。kernelのopen file descriptionに接続され、offsetやstatus flagsはそこに属します。fd番号は永続的なidentityではありません。

## OS内部では何が起きているか

fd tableはprocessの索引で、kernel objectの実体ではありません。closeするとslotが空き、次のopenで再利用されます。標準fdも通常のdescriptorです。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`openat, read, write, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.posix.fd_t / openat / read、std.os.linux.write / close`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
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
man 2 open
man 2 read
man 2 write
man 2 close
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

stdoutへ直接writeし、stdinを一度readする。hello.txtを開き、fd番号をstderrへ表示する。さらに3ファイルを同時に開く。

## 実装手順

1. 章ディレクトリでmain.zigを作り、editorで開く。
2. 標準ライブラリをimportする。@importとライブラリ名stdを調べる。
3. entry pointとなる公開main関数を定義する。返却型とerror unionの意味を確認する。
4. まず空のmainを実行できる状態にし、コンパイラの診断を読んで修正する。
5. Linuxのwriteの宣言を探す。fd=1へ短い文字列を出し、返却値と実際のbyte数を確認する。
6. zig runで出力を確認後、build-exeで生成したbinaryをstraceし、fd=1へのwriteを見つける。
7. stdinからreadし、有効なbyte範囲だけstdoutへ返す。
8. hello.txtをopenしfdをstderrへ記録する。3ファイル同時openと中間fdのclose・再openを試す。
9. 成功直後に解放責任を決め、closeを観測する。

## 実行

この章のLinux環境内でファイルを作り、最初の行から自分で書きます。

```sh
touch main.zig
$EDITOR main.zig
zig run main.zig
```

$EDITORは事前に設定したeditor名です（例: nvim）。コンパイラエラーも教材の一部です。
型、error union、optional、integer cast、pointer、alignment、sliceの要求を読み、修正して再実行します。
引数がある課題は`zig run main.zig -- 引数`で渡します。

## 手動で確認

まずstdoutの短い文字列を確認します。stdinを追加したらterminal入力とEOF（Ctrl-D）を試してください。

```sh
zig build-exe main.zig
printf 'input\n' | ./main > output.txt
cat output.txt
printf 'file data\n' > hello.txt
```

openの課題では実験用fileを3つ作り、fd番号はstderrへ記録します。stdout redirect後もfd=1を使う意味を説明します。

## 観察ポイント

stdoutをファイルへredirectした場合と端末の場合でfd=1の参照先を比較する。/proc/<pid>/fdを調べる。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

普段は`zig run main.zig`、観察時は先にbinaryを生成します。

```sh
zig build-exe main.zig
strace -f -tt -T -o trace.log ./main
strace -f -c ./main
```

引数がある課題は`./main`の後に付けます。serverは別terminalでclientを接続し、終了後の集計を読みます。
`zig run`自体をtraceするとcompilerとlinkerのsyscallが混ざるため、学習対象binaryだけを観測します。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
program初期化と自分の処理の違いも調べます。[観察手順](../docs/debugging.md)。

## よくある失敗

fd=3が必ず最初になると仮定する／closeしたfdを使う。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `posix.zig / os/linux.zig`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

deferは取得成功直後に置く。複数取得の途中失敗にはerrdeferで所有権を整理する。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

端末・redirect・複数openの3つの図とtraceを記録し、fd再利用を説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

dupしたfdでoffsetの共有を実験する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> read/writeは1回で全データを転送するのでしょうか？

## fdの図を完成させる

```text
Processのfd table (kernel管理)       Kernel objects
fd番号をuserspaceが指定              open file descriptions
0 ───────────────────────────────> terminal stdin
1 ───────────────────────────────> terminal stdout
2 ───────────────────────────────> terminal stderr
3 ───────────────────────────────> hello.txt (offset / status flags)
```

予想: 0/1/2が開いている場合、次のopenでどの整数が返るか？
実験: 3ファイルを開いた後、中間のfdだけcloseしてもう1ファイルを開きます。
確認: 「fd番号」「ファイル名」「offset」「close責任」を別々に書きます。
stdoutへ`hello\n`、stdinで得たbyteをstdoutへ返すところから始めてください。
診断情報はstderrへ出すと、stdout redirectの実験が汚れません。

## Zig CLIの最初の一歩

`touch`は空fileを作るだけです。空fileを実行してentry pointの診断を見ることも学習になります。
stdを使う行は@importと名前stdから自分で組み立てます。mainの公開性、返却型、errorを返す可能性を調べてください。
最初はstdoutへ出す短いbyte列だけに絞り、fd 1、buffer pointer、長さ、返却値を紙に書きます。
最初から引数取得や便利な出力helperを作る必要はありません。

```sh
cd 01-file-descriptor
touch main.zig
$EDITOR main.zig
zig run main.zig
zig build-exe main.zig
strace -e trace=write ./main
```

このcdはrepo rootから行います。Linux内でeditor・コンパイラ・実行・straceを揃えます。
エラーは該当行、expected/found型、error unionの処理要求を読んでから直します。
`zig build-exe`はcompileしてbinaryを作り、実行しません。`./main`がそのprogramです。
`strace zig run ...`ではcompiler/linkerまで含まれるため、上のように二段階に分けます。
