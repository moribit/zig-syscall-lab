# Chapter 03: Blocking TCP

## この章で学ぶこと

TCP byte stream、socket lifecycle、blocking。

## 前章とのつながり

ファイル転送のloopをTCPへ適用します。

## 背景

listen socketとaccepted socketは別fdです。acceptは接続、readは受信データを待ちます。TCPはmessage境界を保存しません。

## OS内部では何が起きているか

listen queueに接続が入りacceptで新しいfdが生まれます。受信queueが空ならblocking readのthreadを待機させ、データ到着で再開します。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`socket, bind, listen, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.socket/bind/listen/accept4/read/sendto`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

127.0.0.1:9000で一度に1接続を処理するecho server。受信したbyteを順序どおり返す。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. bind→listen→accept→read/write loop→EOF→close→次のaccept。IPv4 addressのnetwork byte orderを確かめる。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

Aを無送信のまま接続しBを接続する。BのechoがA切断まで進まないことを確認する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-03
strace -f -c ./zig-out/bin/lab-03
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

1 read = 1 messageと思う／listen fdへreadする／peer切断後のsendでSIGPIPE。

## ヒント

C ABIのsockaddrはextern layout。sendtoのMSG.NOSIGNAL等でSIGPIPE方針を明示する。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

通常echo・binary・切断後の再接続が通り、待ち箇所をtraceに示せる。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

backlogとアプリが処理可能な接続数の違いを調べる。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-03`も試します。

## 次章への問い

> 待つreadをやめると複数接続を進められますか？

## 待機の図

```text
client A → accept → read ← Aが送信するまで待つ → write
client B → kernelの待機queue … アプリはまだacceptへ戻らない
```

Bのconnect成功だけではBのecho処理開始を意味しません。
accept queue、アプリが所有するconnection、readの待機を区別します。
