# Chapter 14: std.Io Async / Concurrency

## この章で学ぶこと

Future、async/concurrent、cancel、Group、structured concurrency。

## 前章とのつながり

Io依存にタスクの寿命を組み込みます。

## 背景

asyncは即時実行・完了も許します。concurrentはcallerがI/O待ち中も進める契約を要求しConcurrencyUnavailableになり得ます。parallelismの保証ではありません。

## OS内部では何が起きているか

Threadedはtaskをthreadへ割当て得ますが、Io.async契約は即時完了も許します。sleepやfutex等のkernel待機とtask scopeの管理は別の層です。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`clone/clone3, futex, clock_nanosleep（実装依存）`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`io.async、try io.concurrent、future.await(io)/cancel(io)、std.Io.Group`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

A/B/Cを異なるdurationでsleepさせ、thread IDと開始/終了時刻を記録する。async/concurrent比較、cancel、Groupによるscope管理を実装する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. taskはIo.Cancelable!void→Io.sleep→Future回収→cancel実験→Group.init→途中errorでも全taskをjoin/cancelする。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

単一thread設定と通常設定を比較。taskの終了順を固定値としてtestしない。cancel後にborrowしたbufferが安全に解放可能か確認する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-14
strace -f -c ./zig-out/bin/lab-14
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

旧言語組込async/await構文／Futureを未回収／Canceledを握り潰す／Groupへ任意error unionを返す。

## ヒント

Future.cancelは取消要求と完了待ちを行いResultを返す。cancel pointがなければすぐ止まらない。Group taskはCancelable!voidへcoerce可能な返却型が必要。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

全task終了がscope exitより前、cancel時cleanup、ConcurrencyUnavailable処理の3試験を作る。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

CPU-bound taskのparallelismとI/O concurrencyを別に測る。同期loggingの影響も測る。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-14`も試します。

## 次章への問い

> readinessとcompletionの違いは高レベルAPIから見えなくなりますか？
