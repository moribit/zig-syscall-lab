# Chapter 12: Event Loop from Scratch

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

register/wait/dispatch/wake、公平性、状態機械。

## 前章とのつながり

08章の次に実施します。io_uringを学ぶ前にepoll loopを抽象化します。

## 背景

sleep中のloopに別threadから仕事を渡すにはwake fdが必要です。queueのpublishとwake通知の順序がlost wakeupを左右します。

## OS内部では何が起きているか

eventfdはcounterを持つfdで、writeによりreadinessを作れます。epollの待機を起こし、userspace queueへpublishした仕事をloopへ渡します。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`epoll_wait, epoll_ctl, eventfd2, read, write`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.eventfd、std.atomic.Value、allocator`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux.zigのeventfdとstd.atomic`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 2 eventfd
man 2 epoll_wait
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

epoll backendの小さなEventLoopを設計する。register/wait/dispatch/wakeの契約を自分で決め、echo logicを移植する。

## 実装手順

1. main.zigで動くepoll serverのregister/wait/dispatch/wakeの責務を図にする。
2. まず単一file内でbackendとserver logicの境界を決める。
3. eventfdでidle中のloopを起こす仕組みを書く。
4. queue publishとwakeの順序、lost wakeupの可能性を調べる。
5. 別threadからstopを要求し、drainとcleanupまで進むか観測する。
6. 責務を理解してからconnection.zigやevent_loop.zigへ分けるか考える。

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

Terminal Aで`zig run main.zig`、Terminal Bで`nc 127.0.0.1 9000`。
echoの確認後、全clientをidleにして別threadからstopを要求します。
wake→dispatch→drain→cleanupの時刻とfd数を記録し、繰り返して取りこぼしを調べます。

## 観察ポイント

idle待機中に別threadからstopを要求。wakeが欠落せずcleanupまで進むかを繰り返す。
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

callbackへstack pointerを渡す／wakeのみ送ってqueueを未公開／handlerがloop全体を長時間占有。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux.zigのeventfdとstd.atomic`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

callbackの連鎖よりtagged unionとstate transitionを検討する。explicit ownershipでevent batchの寿命を限定する。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

複数echo、idle stop、wakeとpublishの順序、stale token対応を実験記録で説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

fn Server(comptime Backend: type) typeという形でPollBackend/EpollBackendを選べるか設計する。完成形は自分で書く。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> ready後にreadする代わりにread自体をkernelへ依頼できますか？ 次は09章です。

## ファイル分割を考える

ここまで単一ファイルで実装しました。分割した方が良い責務はありますか？
connection.zigやevent_loop.zigを自分で作る場合も、まず重複とownershipの境界を説明してください。
最初からSocketやConnectionManagerのhelperを置かず、ベタ書き→理解→重複→抽象化の順に進めます。
