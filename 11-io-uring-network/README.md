# Chapter 11: io_uring Network

## この章で学ぶこと

accept/recv/send completion、operation lifecycle。

## 前章とのつながり

fileのcompletion管理をsocketへ応用します。

## 背景

recv完了までbufferはkernelから参照されます。closeやcancel要求だけでoperationの完了を見なしてはいけません。

## OS内部では何が起きているか

accept completionは新client fd、recv/send completionは転送結果です。operationはconnection stateより長く残り得るため、close後のCQEも回収計画が必要です。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`socket, bind, listen, io_uring_enter, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.IoUring.accept/recv/send/cancel（確認用）`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

単発accept・recv・sendのecho。最初は1接続、次に複数接続とoperation tokenを導入する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. accept submit→CQEでclient fd取得→recv→send→partial send残量→次recv。切断時はin-flightを回収してからstate解放。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

socket read/writeがtraceに出なくてもoperationはkernel内で行われることを説明する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-11
strace -f -c ./zig-out/bin/lab-11
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

CQEをfdだけで識別／同一bufferへ複数recv／cancel完了と対象operation完了を混同。

## ヒント

connection ID、世代、operation種をuser_dataに符号化する。pointerを使う場合はalignmentと寿命を文書化する。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

tools/check.py echo --multiと切断時in-flight試験が通る。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

multishot acceptをfeature probe後に試し、CQE F_MOREと最終完了の意味を調べる。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-11`も試します。

## 次章への問い

> 自作loopの責務をstd.Ioはどう表しますか？ 次は13章です。
