# Chapter 07: epoll Echo Server

## この章で学ぶこと

connection state、pending write、event dispatch。

## 前章とのつながり

06の実験をserverのloopへ育てます。

## 背景

1回のeventで複数connectionをdispatchします。readinessは後続操作の成功保証ではなく、EAGAINまでの進捗機会です。

## OS内部では何が起きているか

各socketには独立した送受信queueがあります。epollが複数ready eventをまとめても、userspace側のconnection stateと未送信offsetは自動管理されません。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`epoll_wait, epoll_ctl, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linuxのepoll/socket API、allocator`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

connectionにfd・世代・受信領域・送信領域・送信済みoffsetを設計する。全clientをnon-blocking echoする。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. wait→event token検証→listenerはaccept drain→clientはread drain→write残量→MODでOUT切替→終了処理。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

slow receiverでOUTが必要な間だけ登録されるか。連続切断でfdが再利用されるか。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-07
strace -f -c ./zig-out/bin/lab-07
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

event batch内の古いpointerを使う／buffer移動後のpointer保持／二重close。

## ヒント

allocationの所有者とpointerの有効期限を図にする。malloc相当はallocatorを明示して行う。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

tools/check.py echo --multiが通り、partial writeのunit testとfd leak確認ができる。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

dispatchの公平性をbyte数または操作数budgetで制限する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-07`も試します。

## 次章への問い

> broadcastで送信量が増えたら遅いclientをどう扱いますか？
