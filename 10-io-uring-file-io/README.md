# Chapter 10: io_uring File I/O

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

非同期read、offset、buffer lifetime、file copier。

## 前章とのつながり

NOPを実データのoperationへ置き換えます。

## 背景

CQE.resは実際の転送量か負のerrnoです。page cacheやkernel workerの影響があるのでasynchronous submissionは常にdisk並列を意味しません。

## OS内部では何が起きているか

kernelは各要求のoffsetとbuffer addressを参照し、転送完了をCQEへ書きます。page cache、device、worker等の経路は環境やopcodeで変わります。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`openat, io_uring_setup, mmap, io_uring_enter, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`自作ring、std.os.linux.IoUring.read/write（比較用）`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux/IoUring.zigのread/writeと自作ring`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 7 io_uring
man 2 read
man 2 write
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

cat PATHの非同期read→複数file read→cp SOURCE DEST。最初は同時in-flight=1、次に明示offsetで複数化する。

## 実装手順

1. 自作ringをmain.zigへ手で移し、NOPを1 fileのreadへ変える。
2. operation ID、offset、bufferの所有者を決め、最初はin-flight=1にする。
3. CQE.resのbyte数か負errnoを読み分ける。
4. cat PATHを実装し、複数fileのreadへ進む。
5. cp SOURCE DESTを追加し、partial read/writeを残量要求へ変換する。
6. 複数in-flightと明示offsetを導入し、completion順と出力順を分離する。
7. 全completion回収前にbufferを再利用していないか所有権の図で確認する。

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

cat/cpのCLIを自分で定義します。

```sh
printf 'uring file\n' > input.txt
zig run main.zig -- cat input.txt
zig build-exe main.zig
./main cat input.txt > output.txt
cmp input.txt output.txt
./main cp input.txt copy.txt
cmp input.txt copy.txt
```

空file、大きなbinary file、既存destへのcopyも試します。02章と同じfile/buffer条件でstrace集計を比較します。
完了順をlogし、出力fileのoffsetとoperation IDを確認します。

## 観察ポイント

02と同じデータでsyscall数を比較。warm cache/cold cacheを区別し、結果をreorderしても出力順を保つ。
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

offset=-1の共有位置を無計画に使う／submit数を転送byte数と思う／write完了前にbuffer再利用。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux/IoUring.zigのread/writeと自作ring`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

ReadBufferはtagged union。まずraw SQE、次にstdlib wrapperで失われる操作を列挙する。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

cat/cpのbyteが一致し、completion順・明示offset・buffer lifetimeを説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

batchサイズ1/8/32でenter回数とlatencyを比較する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> socketではEOF・切断・cancelとin-flight所有権がどう絡みますか？
