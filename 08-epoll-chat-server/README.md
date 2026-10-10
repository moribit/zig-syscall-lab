# Chapter 08: epoll Chat Server

## この章で学ぶこと

backpressure、slow client、broadcast、lifecycle。

## 前章とのつながり

echoから他connectionへの出力へ広げます。

## 背景

送信先ごとに進捗が異なります。無制限queueは遅いclientによってメモリを使い尽くします。TCP flow controlだけではアプリqueueを制限できません。

## OS内部では何が起きているか

kernel送信queueが詰まるとsendは短くなるかEAGAINになります。userspace queueを無制限にするとkernelのflow controlだけではmemory増加を防げません。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`epoll_wait, epoll_ctl, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`allocator、optional、tagged unionとLinux epoll`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

newline区切り、最大4096 byteのmessageを他clientだけへbroadcast。未送信queue上限64KiBで遅いclientを切断する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. byte streamからframe組立→長さ制限→各receiverへenqueue→OUT切替→flush→EOF/overflow時cleanup。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

1 receiverを読まないままbroadcastを続ける。RSSとqueue長を測り、他clientの進捗を確認する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-08
strace -f -c ./zig-out/bin/lab-08
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

送信者bufferを共有したまま上書き／切断中に配列をiterate／無制限buffer。

## ヒント

共有messageを使うなら参照数、copyなら各queueの所有権と費用を示す。まず明確なcopy方式を選んでもよい。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

tools/check.py chatが通り、slow client切断とqueue上限の追加試験を提出する。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

high/low watermarkで入力をpause/resumeする別方針を比較する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-08`も試します。

## 次章への問い

> dispatchの共通部分をOS APIから分離できますか？ 次は12章です。
