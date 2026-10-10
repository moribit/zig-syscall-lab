# Capstone: Linux TCP Serverを設計する

## この章で作るもの

自分で以下を作成します。この教材からソースコードは提供しません。

```text
main.zig
report.md
```

まず単一Zig fileで進め、責務と重複を理解した後に分割するか決めます。

## この章で学ぶこと

backend選択、所有権、lifecycle、backpressureを一つの設計へまとめます。

## 前章とのつながり

benchmarkの数字とI/Oモデルの意味を使い、要件に合うbackendを選びます。

## 背景

外部ライブラリなしのZig 0.17.0で、Linux上で複数clientを処理するTCP serverを自作します。
backendはepoll / io_uring / std.Ioから選択。byte echoかnewline chatを選び、先に仕様を書きます。

## OS内部では何が起きているか

fd table、kernel socket buffer、アプリqueue、in-flight operationの所有者を図にします。

## 今回使うsystem call

socket/bind/listenと選択backendの待機/転送syscall。実測で一覧を作ります。

## Zigからどう見えるか

allocatorとIo/backendを明示依存にします。C ABI layoutとpointer寿命も説明します。

## stdlibを読む

zig envのstd_dirからos/linux.zig、Io.zig、選択backendのsourceを開きます。
関数型、error set、Linux固有実装、libc経由か、syscallへどう降りるかを確認します。
[API索引](../docs/api-audit.md)から名前を探し、引数を自分で組み立てます。

## man pageを読む

```sh
man 2 socket
man 2 accept
man 2 read
man 2 send
man 7 epoll
man 7 io_uring
```

選択backendに必要なページで戻り値、errno、短い転送、切断、resource寿命を確認します。

## 実装課題

explicit memory allocation、explicit connection lifecycle、graceful disconnect、backpressure、
partial read/write、error handlingを全て満たします。message/queue上限とslow client方針を仕様化します。

## 実装手順

1. 前章と同様にmain.zigを自分で作る。
2. report.mdにprotocol、上限、終了条件、backend選択理由を書く。
3. connectionとoperationの状態機械、所有権、cleanup順を描く。
4. importとmainから手書きし、1接続を動かす。
5. 複数→slow client→切断→resource exhaustionの順に実験する。
6. compilerの型・error union・pointer/alignment診断を読んで修正する。
7. 生成binaryのtraceと性能データを保存する。

## 実行

Linuxのこの章のディレクトリで作業します。

```sh
touch main.zig
$EDITOR main.zig
zig run main.zig
```

$EDITORにはnvim等を設定します。教材に埋めるための既存コードはありません。

## 手動で確認

Terminal Aで`zig run main.zig`、別terminalで`nc 127.0.0.1 9000`を複数起動します。
正常echo/chat、idle client、half-close、再接続を確認します。
読まないreceiver、送信中の切断、queue上限、終了時drainも試します。
短いwriteやEAGAINが自然に出ない場合は、実験用に転送量制限や失敗注入を自分で加えて記録します。

## 観察ポイント

FD/RSSの長時間増加、10,000接続時の容量、queue budget、公平性、cancel時のbuffer寿命。

## straceで確認

```sh
zig build-exe main.zig
strace -f -tt -T -o trace.log ./main
strace -f -c ./main
```

zig run自体のcompiler/linkerを混ぜず、学習対象だけを観測します。
別terminalでclientを動かし、syscall回数とblocking地点を説明します。

## よくある失敗

性能だけでbackend選択、cleanup時のin-flight忘れ、無制限queue、fd再利用の誤認。

## ヒント

### Hint 1

まず1接続、1 byte、1 operationで正常系と所有権を確立します。

<details>
<summary>Hint 2</summary>

ready通知後にアプリがI/Oするのか、submit済みI/Oのcompletionを回収するのかを図にしてください。

</details>

<details>
<summary>Hint 3</summary>

close/cancel要求だけでkernelや子taskからの参照が消えたとは仮定しません。
最後の参照が終わる地点とbuffer解放をsourceとtraceに結び付けてください。

</details>

## 完了条件

全resourceの所有者と解放地点を説明でき、手動実験の入力・期待・実際が記録されていること。
report.mdに以下を回答します。

- なぜそのbackendを選んだか
- どこでsyscallが発生するか
- blocking pointはどこか
- memory ownershipはどうなっているか
- 10,000 connectionでは何が問題になるか

## レポートの見出し

仕様 / backend選択 / syscallとblocking point / ownership図 / 10,000接続の容量計画 /
手動実験の結果 / 残る制約。
自作main.zigとreport.mdはそのままcommitして構いません。

## 発展課題

2 backendで同じprotocolを動かし、運用条件と測定結果によって選択が変わるか議論します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat ./main
```

## 次章への問い

> 次のOSや異なるprotocolでも、どの契約は再利用でき、どの契約は設計し直す必要がありますか？
