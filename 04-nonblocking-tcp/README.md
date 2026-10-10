# Chapter 04: Non-blocking TCP

## この章で学ぶこと

O_NONBLOCK、EAGAIN/EWOULDBLOCK、busy loop。

## 前章とのつながり

blockingによる停止を明示的な状態へ変えます。

## 背景

non-blockingは待てない状況でEAGAINを返します。LinuxではEWOULDBLOCKとEAGAINは同値。既に受信済みなら正常に読めます。

## OS内部では何が起きているか

受信queueが空でも呼出threadをsleepさせずAGAINを返します。非blocking flagはopen file descriptionに属し、accepted fdはlistenerからの自動継承を仮定しません。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`fcntl, accept4, read, sendto`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.fcntl / O / SOCK.NONBLOCK、std.posix.readのerror.WouldBlock`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

最大3接続を順にscanするecho。意図的にbusy loopを作り、未送信時のCPUを測る。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. listenerとaccepted fd両方をnon-blocking化→接続配列→readとpending write→EAGAINなら別fdへ。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

idle時のread回数、CPU、1接続だけ送信した場合の空振り数を数える。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-04
strace -f -c ./zig-out/bin/lab-04
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

acceptのNONBLOCKをlistenerだけに設定／WouldBlockで切断／pending byteを破棄。

## ヒント

optionalは空slot、error unionは待てない状態を区別するために使う。fcntlでは既存flagsを保つ。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

3接続が進み、CPU浪費を再現して説明できる。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

送信bufferを小さくしてpartial sendを誘発する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-04`も試します。

## 次章への問い

> readyなfdだけ知る方法はありませんか？
