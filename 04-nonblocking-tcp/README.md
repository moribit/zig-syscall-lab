# Chapter 04: Non-blocking TCP

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

O_NONBLOCK、EAGAIN/EWOULDBLOCK、busy loop。

## 前章とのつながり

blockingによる停止を明示的な状態へ変えます。

## 背景

non-blockingは待てない状況でEAGAINを返します。LinuxではEWOULDBLOCKとEAGAINは同値。既に受信済みなら正常に読めます。

## OS内部では何が起きているか

受信queueが空でも呼出threadをsleepさせずAGAINを返します。非blocking flagはopen file descriptionに属し、accepted fdはlistenerからの自動継承を仮定しません。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`fcntl, accept4, read, sendto`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.fcntl / O / SOCK.NONBLOCK、std.posix.readのerror.WouldBlock`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux.zigのfcntl・accept4とposix.zigのread`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 2 fcntl
man 2 accept
man 2 read
man 2 send
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

最大3接続を順にscanするecho。意図的にbusy loopを作り、未送信時のCPUを測る。

## 実装手順

1. listenerとaccepted fdをそれぞれnon-blockingにする。
2. 最大3 connectionを保持し、各fdを順番にreadするloopを書く。
3. EAGAINを切断と区別して次のfdへ進む。
4. pending writeと送信済みoffsetを保持する。
5. 全clientをidleにしたbusy loopのCPUとread回数を測る。
6. bufferや送信速度を変え、partial I/O後もbyteが失われないか確認する。

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

Terminal Aで`zig run main.zig`、別の3 terminalで`nc 127.0.0.1 9000`を使います。
全clientをidleにしてCPUを観測し、一つだけ送信した時の空振りread数を数えます。
最大3接続という今回の制限を超えないでください。

## 観察ポイント

idle時のread回数、CPU、1接続だけ送信した場合の空振り数を数える。
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

acceptのNONBLOCKをlistenerだけに設定／WouldBlockで切断／pending byteを破棄。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux.zigのfcntl・accept4とposix.zigのread`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

optionalは空slot、error unionは待てない状態を区別するために使う。fcntlでは既存flagsを保つ。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

3接続が進み、EAGAINとEOFを区別し、CPU浪費を再現して説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

送信bufferを小さくしてpartial sendを誘発する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> readyなfdだけ知る方法はありませんか？
