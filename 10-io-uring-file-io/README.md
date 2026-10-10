# Chapter 10: io_uring File I/O

## この章で学ぶこと

非同期read、offset、buffer lifetime、file copier。

## 前章とのつながり

NOPを実データのoperationへ置き換えます。

## 背景

CQE.resは実際の転送量か負のerrnoです。page cacheやkernel workerの影響があるのでasynchronous submissionは常にdisk並列を意味しません。

## OS内部では何が起きているか

kernelは各要求のoffsetとbuffer addressを参照し、転送完了をCQEへ書きます。page cache、device、worker等の経路は環境やopcodeで変わります。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`openat, io_uring_setup, mmap, io_uring_enter, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`自作ring、std.os.linux.IoUring.read/write（比較用）`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

cat PATHの非同期read→複数file read→cp SOURCE DEST。最初は同時in-flight=1、次に明示offsetで複数化する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. operation IDとbufferを割当→read submit→CQEで長さ確認→write submit→partial完了で残量再要求→全完了後解放。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

02と同じデータでsyscall数を比較。warm cache/cold cacheを区別し、結果をreorderしても出力順を保つ。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-10
strace -f -c ./zig-out/bin/lab-10
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

offset=-1の共有位置を無計画に使う／submit数を転送byte数と思う／write完了前にbuffer再利用。

## ヒント

ReadBufferはtagged union。まずraw SQE、次にstdlib wrapperで失われる操作を列挙する。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

tools/check.py cat/cpが通り、out-of-orderとpartial CQEを注入したunit testを持つ。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

batchサイズ1/8/32でenter回数とlatencyを比較する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-10`も試します。

## 次章への問い

> socketではEOF・切断・cancelとin-flight所有権がどう絡みますか？
