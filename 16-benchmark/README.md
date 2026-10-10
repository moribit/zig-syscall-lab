# Chapter 16: Benchmark

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

throughput、p50/p95/p99、CPU/RSS、syscall、context switch。

## 前章とのつながり

同じ仕様のbackend比較を測定へ進めます。

## 背景

観測tool自身が負荷を変えます。trace付きrunを通常latency runと混ぜず、接続確立とsteady stateも分けます。

## OS内部では何が起きているか

実行時間にはuserspace処理、syscall、待機、scheduler、cacheの影響が重なります。context switchとCPU消費はlatencyと同じ値ではありません。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`各backendのI/O syscall、futex、clone/clone3`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`ReleaseFast/ReleaseSafe、明示allocator、std.Io.Clock`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `Io.zigのClockと各backendの待機/転送経路`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 1 perf-stat
man 1 time
man 1 strace
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

blocking/thread-per-client/poll/epoll/io_uring/std.Ioを可能な範囲で比較する。負荷生成側も自作し、同じpayloadとclient数を使う。

## 実装手順

1. main.zigへserver/clientのmodeを自分で定義し、同じecho負荷を作れるようにする。
2. clientは固定長requestと同じ長さのreplyを対応させ、TCPのread境界をrequest数に使わない。
3. setupとwarmupを計測区間から分け、単調clockで成功requestの往復時間を記録する。
4. timeoutと失敗数を保存し、p50/p95/p99、成功requests/secと転送byte数/secを計算する。
5. 条件を固定し最低5反復、client数1/10/100、payload64/4096で比較する。
6. 別runでstrace/perf/timeを使い、serverと負荷生成器のCPUを分けて観察する。

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

serverと負荷生成modeのCLI契約は自分で決めます。既存toolだけの大量送信ではrequest latencyが測れない場合があります。
少量のechoをncで確認した後、自作clientで固定長replyを待って次requestを送るclosed-loop測定を行います。
測定結果をCSVに保存し、失敗数を残してpercentileと反復間分散を計算します。
wrkはHTTP用、iperfは別protocolなのでその数値をraw TCP echoのlatencyとして扱いません。

## 観察ポイント

CPUとRSSはserver/client別。strace -cのcall数を成功request数で割る。外れ値と失敗を捨てない。
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

wrkをraw TCP echoへ使う／iperfとechoを同一負荷と思う／異なるbuild mode／平均だけ比較。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `Io.zigのClockと各backendの待機/転送経路`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

wrkはHTTP用、iperfは別protocolの帯域参考。負荷生成器自身もbottleneckになり得る。未実装backendはN/Aで理由を残す。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

機能確認後に測定し、CSV、環境条件、反復間分散、p50/p95/p99、失敗数をレポートできる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

perf statでcontext-switches,cpu-migrations,page-faults,cycles,instructionsを測る。権限不足も記録する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> capstoneで何を選び、10,000接続時の限界をどう説明しますか？

## コンパイラ設定を固定する

Debugは安全性検査とdebug情報を含む基本設定です。ReleaseFastでは最適化と安全性検査の扱いが変わります。
最初にDebugで挙動を確認し、測定では全backendを同じ設定でcompileします。

```sh
zig build-exe main.zig
zig build-exe -O ReleaseFast main.zig
```

二つ目のコマンドは同名binaryを置き換えます。異なる設定を比較するなら-femit-binで名前を分けてください。
ReleaseSafeも比較対象にでき、modeを必ず記録します。性能測定にも正しい結果と失敗数の確認が必要です。

## 測定する値

| 値 | 測定の契約 |
|---|---|
| requests/sec | 測定区間内の成功reply数 / 秒。固定長replyを全て受信して1件 |
| throughput | 成功payload byte数 / 秒。片方向か往復か明記 |
| p50/p95/p99 | 成功requestの往復時間の分位数。失敗数は別に残す |
| CPU/RSS | serverと自作負荷生成器を別々にpidstat等で観測 |
| syscalls | 別runのstrace -c。成功request数と条件も記録 |
| context switches | 別runのperf stat。利用不可counterはN/A |

負荷生成器はmain.zigの自作modeから始め、必要になってからclient.zigへ分けても構いません。
固定client数、payload長、測定期間、warmup、timeoutをCLIまたは定数で明示します。
clockは単調時刻を使い、測定区間外の接続開始とwarmupを混ぜない設計にしてください。
closed-loopは遅延中に新しいrequestを出さないため、open-loop負荷との差も発展課題にします。
Python等の配布helperは使いません。自作clientもbottleneckになり得るのでCPUと実際の送信量を測ります。
thread-per-client版も必要なら自分で作り、未実装backendはN/Aと理由を残します。

```sh
pidstat -p <server-pid> 1
```

上の<server-pid>は実際の整数に置き換えます。外部toolやhardware counterは必須依存にしません。
