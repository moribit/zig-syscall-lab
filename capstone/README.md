# Capstone: Linux TCP Serverを設計する

## この章で学ぶこと

backend選択、所有権、lifecycle、backpressureを一つの設計へまとめます。

## 前章とのつながり

benchmarkの数字とI/Oモデルの意味を使い、要件に合うbackendを選びます。

## 背景

外部ライブラリなしのZig 0.17.0で、Linux上で複数clientを処理するTCP serverを自作します。
backendはepoll / io_uring / std.Ioから選択。protocolはbyte echoかnewline chatから選び、先に仕様を書きます。

## OS内部では何が起きているか

fd table、kernel socket buffer、アプリqueue、in-flight operationの所有者を図にします。

## 今回使うsystem call

socket/bind/listenと選択backendの待機/転送syscall。実測で一覧を作ります。

## Zigからどう見えるか

allocatorとIo/backendを明示依存にします。C ABI layoutやpointer寿命も説明します。

## 実装課題

explicit memory allocation、explicit connection lifecycle、graceful disconnect、backpressure、
partial read/write、error handlingを全て満たします。message/queue上限とslow client方針を仕様化します。

## 実装手順

1. protocol、上限、終了条件、backend選択理由をreport.mdに書く。
2. connectionとoperationの状態機械、所有権、cleanup順を描く。
3. 1接続→複数→slow client→切断→resource exhaustionの順に実装する。
4. unit testと外部仕様検査を行い、trace/性能データを保存する。

## 観察ポイント

FD/RSSの長時間増加、10,000接続時の容量、queue budget、公平性、cancel時のbuffer寿命。

## straceで確認

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-capstone
strace -f -c ./zig-out/bin/lab-capstone
```

別terminalのclientで正常・idle・slow・切断を試し、syscall回数とblocking地点を説明します。

## よくある失敗

性能だけでbackend選択、cleanup時のin-flight忘れ、無制限queue、fd再利用の誤認。

## ヒント

最低構成で正しさを確立してから最適化します。完成コードはありません。

## 完了条件

仕様とtestが対応し、全resourceの所有者と解放地点を説明できること。設計レポートに以下を回答します。

- なぜそのbackendを選んだか
- どこでsyscallが発生するか
- blocking pointはどこか
- memory ownershipはどうなっているか
- 10,000 connectionでは何が問題になるか

正常echo/chatに加え、half-close、RST、短いwrite、EAGAIN、slow client、終了時drainの試験を提出します。
`zig build test`はstarter時SKIP。実装後はcontract.zigのTODOへassertionを書きます。

## 発展課題

2 backendで同じprotocolを動かし、運用条件と測定結果によって選択が変わるか議論します。

## 次章への問い

> 次のOSや異なるprotocolでも、どの契約は再利用でき、どの契約は設計し直す必要がありますか？
