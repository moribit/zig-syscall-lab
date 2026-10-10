# Chapter 16: Benchmark

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

## 実装課題

blocking/thread-per-client/poll/epoll/io_uring/std.Ioを可能な範囲で比較する。tools/bench.pyで同じpayloadとclient数を使う。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. kernel/CPU/Zig/commit記録→warmup→最低5反復→client 1/10/100→payload 64/4096→timeoutとerror数→統計→別runでtrace/perf。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

CPUとRSSはserver/client別。strace -cのcall数を成功request数で割る。外れ値と失敗を捨てない。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-16
strace -f -c ./zig-out/bin/lab-16
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

wrkをraw TCP echoへ使う／iperfとechoを同一負荷と思う／異なるbuild mode／平均だけ比較。

## ヒント

wrkはHTTP用、iperfは別protocolの帯域参考。Python負荷生成器もbottleneckになり得る。未実装backendはN/Aで理由を残す。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

testを先に通し、CSV/JSONと測定条件・反復間分散・p99・失敗数をレポートする。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

perf statでcontext-switches,cpu-migrations,page-faults,cycles,instructionsを測る。権限不足も記録する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-16`も試します。

## 次章への問い

> capstoneで何を選び、10,000接続時の限界をどう説明しますか？
