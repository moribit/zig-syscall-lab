# Chapter 15: Reactor vs Proactor

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

同一仕様の比較、comptime backend。

## 前章とのつながり

実装とtraceからモデルを言語化します。

## 背景

epollはreadyを返しアプリがI/O、io_uringはI/O要求を受けcompletionを返します。completionがあることと常にnon-blockingな内部実装は別です。

## OS内部では何が起きているか

reactorでは通知後のアプリのread/writeが転送を依頼します。proactorでは先にsubmitされた転送の結果が返ります。bufferが必要になる時期も違います。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`read/write, poll, epoll_wait, io_uring_enter`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`Server(comptime Backend: type)、error unionとtagged union`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `自分のbackendとIo.zigのvtable契約`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 7 epoll
man 7 io_uring
man 2 poll
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

同一echo protocolをblocking/poll/epoll/io_uring/std.Ioで比較する表を完成。最低2 backendを同じserver logicで動かす。

## 実装手順

1. main.zigで最低2 backendの同一echo仕様を自分で用意する。
2. readiness eventとcompletion resultの契約差を紙に書く。
3. byte stream、queue上限、ownershipの共通部分を決める。
4. 重複に気付いた箇所だけを抽象化する。comptime Backendという型引数を検討する。
5. 同じ入力の出力とtraceを比較し、抽象化で残した差を説明する。

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

選んだbackendをmain.zigの設定か自作CLIで切り替えます。
各backendへ`nc 127.0.0.1 9000`から同じbyteを送り、結果を比較します。
idle、half-close、slow receiverも同じ条件で試し、待機地点とbuffer寿命の違いを表にします。

## 観察ポイント

readを行う主体、wait地点、buffer寿命、cancel方法を各backendで図にする。
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

proactorを必ずzero-copyと思う／epollがO(1)なら全serverもO(1)と思う／APIだけを同形にする。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `自分のbackendとIo.zigのvtable契約`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

comptimeはbackend契約をcompile時に検査できる。readinessとcompletionの意味の違いは隠す前に明示する。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

同一入力で2 backendの結果が一致し、モデル差を残したinterface設計を説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

PollBackend/EpollBackend/UringBackendに必要な能力をcomptimeで検査する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> 速さを公平に測るには何を固定する必要がありますか？
