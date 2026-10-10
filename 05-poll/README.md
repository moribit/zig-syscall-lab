# Chapter 05: poll

## この章で学ぶこと

pollfd、POLLIN/POLLOUT、O(n) scan。

## 前章とのつながり

busy loopの待機をkernelへ任せます。

## 背景

pollは毎回渡された配列を調べ、reventsを更新します。readyでも次のreadが必ず成功する保証はありません。

## OS内部では何が起きているか

kernelはpollへ渡されたfd配列を調べ、必要ならwait queueへ待機者を結び付けます。復帰後もアプリが全reventsをscanする仕事が残ります。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`poll, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.posix.poll / pollfd / POLL`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

non-blockingな複数client echo。pending writeがあるfdだけPOLLOUTを要求する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. pollfd配列→poll timeout→revents判定→accept/read/write→切断slot更新。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

1/100/1000 idle接続で配列長とready数、処理時間を記録する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-05
strace -f -c ./zig-out/bin/lab-05
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

eventsとreventsを混同／POLLHUPだけで残データを捨てる／常時POLLOUT。

## ヒント

ERR/HUP/NVALも調べる。通常fileはいつもreadyで、disk I/Oの待ちをpollで解消できるとは限らない。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

tools/check.py echoが通り、idle時にpollで待っている。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

swap-removeによるslot変更時のfdとstate対応を検証する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-05`も試します。

## 次章への問い

> 毎回全fd配列を渡す必要はありますか？
