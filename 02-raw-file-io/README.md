# Chapter 02: Raw File I/O

## この章で学ぶこと

partial read/write、EOF、EINTR、error union。

## 前章とのつながり

fdを持てたので、byte streamを最後まで転送します。

## 背景

要求長と返却長は別です。readの0は非空bufferでEOFを示し、writeの正の短い返却値は進捗です。

## OS内部では何が起きているか

kernelはfile offsetからデータをbufferへコピーし、実際の転送量だけoffsetを進めます。signalやpipe容量で要求全量に達しない場合があります。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`openat, read, write, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.posix.openat/read と std.os.linux.read/write/errno`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

CLI cat PATH と cp SOURCE DEST を実装する。空・binary・大きなファイルを処理する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. 固定長buffer→read結果の有効範囲→write残量→EOF→close。cp先はcreate/truncate、元と同一ファイルへのコピーは拒否する。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

1 byte bufferと64KiB bufferでsyscall回数を予想し比較する。pipeでも試す。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-02
strace -f -c ./zig-out/bin/lab-02
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

buffer全体を書く／partial write後にoffsetを進めない／closeをEINTRで盲目的に再試行する。

## ヒント

std.posix.readはINTRを内部でretryする。生linux.readではerrnoを自分でdecodeする。writeが0で残量がある場合の停止方針を決める。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

tools/check.py cat/cpの仕様検査と、短いwriteを注入した自作unit testが通る。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

signalとpipeでEINTRを観察し、SA_RESTARTの影響を記録する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-02`も試します。

## 次章への問い

> fileとsocketは同じread/writeでも待ち方がどう変わりますか？
