# Zig I/O Lab

## Why this repository exists

OSとユーザー空間の境界を、予想・実装・syscall観測から学ぶZig 0.17.0の教材です。
完成サンプル集ではありません。全starterは未実装で、解答コード・外部Zig package・liburing依存はありません。

## Learning philosophy

学習者がコードを書きます。短い転送、切断、所有権、待機地点を自分で説明できることを成果とします。
Zigのerror union、defer、allocator、comptimeはOSの問題を扱う道具として登場します。

## Roadmap

章番号はテーマの識別子です。学習順は **01→02→03→04→05→06→07→08→12→09→10→11→13→14→15→16→capstone**。
12章のevent loopをio_uringより先に行います。[ロードマップ](docs/roadmap.md)。

## Requirements

- Zig **0.17.0**（dev版やmaster版ではなく、このversionのstdlibを読む）
- 実験環境: Linux x86_64 / aarch64。starterのbuild/testはmacOSでも可能
- syscall観測: strace。追加の挙動検査・負荷生成: Python 3標準ライブラリのみ
- perf、pidstat、ss、time、hyperfine等は任意。外部benchmark toolは必須依存にしない

## Linux setup

LinuxでZigを[公式配布](https://ziglang.org/download/0.17.0/)から用意し、`zig version`を確認します。
Debian/Ubuntuなら`sudo apt install strace python3`、perf等は必要な時だけ導入します。
macOSではLima、UTM、Linux VM、Docker/Podman、remote Linuxを使えます。
VM内でrepoをclone/共有しLinux版Zigでbuildしてください。macOS binaryをLinuxへコピーしても動きません。
containerはホストのLinux kernelを共有し、macOSのcontainer実行環境にはLinux VMが入ります。
io_uringはkernel version、sysctl、seccomp、resource制限により利用できない場合があります。
`EPERM/ENOSYS/EOPNOTSUPP`を記録し、利用可能なLinux VM/remote環境へ移る選択もあります。
詳しくは[Linux I/O](docs/linux-io-overview.md)。

## How to study

1. 章READMEを読む。
2. コードを書かず図と所有権を理解する。
3. syscallと返却値を予想してnotes.mdへ書く。
4. 自分で最小ケースを実装する。
5. straceする。
6. 予想との差とblocking地点を説明する。
7. 発展課題を行い、次章への問いに答える。

```sh
zig build
zig build test --summary all
zig build chapter -Dchapter=06
zig build test -Dchapter=06
cd 01-file-descriptor
zig build
zig build test --summary all
```

root buildは17のstarterをcompile/installします。rootのtestは17の契約testを実行し、未実装時はSKIPです。
選択buildでは`zig-out/bin/lab-06`のような名前になります。cross compile例:
`zig build -Dtarget=x86_64-linux` / `zig build -Dtarget=aarch64-linux`。
cross compileしたtestはそのLinux target上で実行します。native macOSのSKIPはLinux動作検証を意味しません。
実装前のbinaryは`error.NotImplemented`で終了します。学習完了はbuild成功やSKIPではなく章の完了条件で判定します。

## Do not copy code

完成実装は置きません。stdlibは契約・ABI・wrapperの処理を読むために使い、アプリのloopは自分で設計します。
`implemented = true`に変更するとtestは`MissingContractTests`で失敗します。
章の状態管理を検証するassertionを追加し、そのTODOを置き換えてください。
[外部仕様検査](tools/README.md)は実装の答えを含まず、実行結果を検査します。

## How to use strace

```sh
strace -f -tt -T -o trace.log ./zig-out/bin/lab-01
strace -f -c ./zig-out/bin/lab-01
```

実装後にLinuxで使います。`-T`でsyscall内の経過時間、`-c`で回数を確認します。
[debugging](docs/debugging.md)に待機・割込・trace負荷の読み方があります。

## Chapters

| 章 | 学ぶこと |
|---|---|
| [01 File Descriptor](01-file-descriptor/README.md) | プロセスとfd table、0/1/2、open/close/read/write |
| [02 Raw File I/O](02-raw-file-io/README.md) | partial read/write、EOF、EINTR、error union |
| [03 Blocking TCP](03-blocking-tcp/README.md) | TCP byte stream、socket lifecycle、blocking |
| [04 Non-blocking TCP](04-nonblocking-tcp/README.md) | O_NONBLOCK、EAGAIN/EWOULDBLOCK、busy loop |
| [05 poll](05-poll/README.md) | pollfd、POLLIN/POLLOUT、O(n) scan |
| [06 epoll Fundamentals](06-epoll/README.md) | interest list、ready list、LT/ET、IN/OUT/ERR/HUP |
| [07 epoll Echo Server](07-epoll-echo-server/README.md) | connection state、pending write、event dispatch |
| [08 epoll Chat Server](08-epoll-chat-server/README.md) | backpressure、slow client、broadcast、lifecycle |
| [09 io_uring Fundamentals](09-io-uring-basics/README.md) | SQ/CQ、SQE/CQE、mmap、submission/completion |
| [10 io_uring File I/O](10-io-uring-file-io/README.md) | 非同期read、offset、buffer lifetime、file copier |
| [11 io_uring Network](11-io-uring-network/README.md) | accept/recv/send completion、operation lifecycle |
| [12 Event Loop from Scratch](12-event-loop/README.md) | register/wait/dispatch/wake、公平性、状態機械 |
| [13 Zig std.Io](13-std-io/README.md) | Io依存注入、Threaded、init.io、backend |
| [14 std.Io Async / Concurrency](14-std-io-async/README.md) | Future、async/concurrent、cancel、Group、structured concurrency |
| [15 Reactor vs Proactor](15-reactor-proactor/README.md) | 同一仕様の比較、comptime backend |
| [16 Benchmark](16-benchmark/README.md) | throughput、p50/p95/p99、CPU/RSS、syscall、context switch |

最後に[capstone](capstone/README.md)でbackend選択と設計レポートを提出します。

## References

[検証記録](docs/verification.md)、[一次資料](docs/references.md)、[API source確認](docs/api-audit.md)、[用語集](docs/glossary.md)。
