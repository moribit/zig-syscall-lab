# Chapter 15: Reactor vs Proactor

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

## 実装課題

同一echo protocolをblocking/poll/epoll/io_uring/std.Ioで比較する表を完成。最低2 backendを同じserver logicで動かす。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. 契約をbyte streamとownershipで定義→ready EventとCompletionの差を定義→共通部分だけ抽象化→trace比較。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

readを行う主体、wait地点、buffer寿命、cancel方法を各backendで図にする。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-15
strace -f -c ./zig-out/bin/lab-15
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

proactorを必ずzero-copyと思う／epollがO(1)なら全serverもO(1)と思う／APIだけを同形にする。

## ヒント

comptimeはbackend契約をcompile時に検査できる。readinessとcompletionの意味の違いは隠す前に明示する。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

同一入力・同一結果と、モデル差を残したinterface設計レポートを提出する。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

PollBackend/EpollBackend/UringBackendに必要な能力をcomptimeで検査する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-15`も試します。

## 次章への問い

> 速さを公平に測るには何を固定する必要がありますか？
