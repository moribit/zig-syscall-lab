# Chapter 14: std.Io Async / Concurrency

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

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

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `Io.zigのasync/concurrent/Future/Group/sleep、Io/Threaded.zig`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 2 futex
man 2 clock_nanosleep
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

A/B/Cを異なるdurationでsleepさせ、thread IDと開始/終了時刻を記録する。async/concurrent比較、cancel、Groupによるscope管理を実装する。

## 実装手順

1. main.zigにIoを受け取るA/B/Cのtaskを自分で定義する。
2. 異なるdurationでsleepし、thread IDと開始/終了時刻を記録する。
3. Io.asyncからFutureを得て、全結果を回収する。
4. Io.concurrentへ変え、ConcurrencyUnavailableと実行順を観測する。
5. Future.cancelを試し、cancel pointとcleanup後の結果回収を確認する。
6. Groupへ移し、途中errorでもscope退出前に全taskを回収する。
7. I/O concurrencyとCPU taskのparallelismを別々に調べる。

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

`zig run main.zig`でtaskごとの開始/終了、thread ID、時刻を記録します。
asyncとconcurrent、単一thread設定と通常設定で繰り返します。終了順を固定の正解にしません。
cancel中のtaskがcleanupしてから親scopeを抜けること、Groupの全taskが回収されることを確認します。

## 観察ポイント

単一thread設定と通常設定を比較。taskの終了順を固定の正解にしない。cancel後にborrowしたbufferが安全に解放可能か確認する。
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

旧言語組込async/await構文／Futureを未回収／Canceledを握り潰す／Groupへ任意error unionを返す。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `Io.zigのasync/concurrent/Future/Group/sleep、Io/Threaded.zig`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

Future.cancelは取消要求と完了待ちを行いResultを返す。cancel pointがなければすぐ止まらない。Group taskはCancelable!voidへcoerce可能な返却型が必要。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

全taskがscope退出前に回収され、cancel時のcleanupとConcurrencyUnavailable処理を説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

CPU-bound taskのparallelismとI/O concurrencyを別に測る。同期loggingの影響も測る。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> readinessとcompletionの違いは高レベルAPIから見えなくなりますか？
