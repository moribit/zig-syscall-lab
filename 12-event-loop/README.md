# Chapter 12: Event Loop from Scratch

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

## 実装課題

epoll backendの小さなEventLoopを設計する。register/wait/dispatch/wakeの契約を自分で決め、echo logicを移植する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. Event/Connectionの状態機械を紙に描く→backend interface→dispatch budget→eventfd wake→停止とdrain。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

idle待機中に別threadからstopを要求。wakeが欠落せずcleanupまで進むかを繰り返す。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-12
strace -f -c ./zig-out/bin/lab-12
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

callbackへstack pointerを渡す／wakeのみ送ってqueueを未公開／handlerがloop全体を長時間占有。

## ヒント

callbackの連鎖よりtagged unionとstate transitionを検討する。explicit ownershipでevent batchの寿命を限定する。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

multi echo、idle stop、stale token、wake raceの試験を作り、backendとserverを分離できる。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

fn Server(comptime Backend: type) typeという形でPollBackend/EpollBackendを選べるか設計する。完成形は自分で書く。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-12`も試します。

## 次章への問い

> ready後にreadする代わりにread自体をkernelへ依頼できますか？ 次は09章です。
