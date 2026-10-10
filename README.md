# Zig I/O Lab

## Why this repository exists

Zig 0.17.0でLinux低レベルI/Oを、予想・手書き・syscall観測から学ぶ教材です。
clone直後の章にはMarkdownだけがあります。import、main、OS API利用も含めて自分でファイルを生み出します。
教材に答えの実装は存在しません。外部Zig packageやliburingにも依存しません。

## Learning philosophy

意図的にbuild.zigを使用しません。1章1ファイル程度の小さなprogramを扱い、
コンパイラを直接使う感覚と短いフィードバックループを重視します。build systemを学習ノイズにせず、OS APIへ集中します。
まずベタ書きし、理解して重複に気付いてから抽象化します。便利なhelperや整った構成を先に作りません。

```text
README → main.zigを自分で作る → zig run main.zig
       → エラーを読む・修正 → binary生成 → strace → 問いに答える
```

## Roadmap

**01→02→03→04→05→06→07→08→12→09→10→11→13→14→15→16→capstone**。
章番号はテーマの識別子です。12章のevent loopを09章のio_uringより先に実施します。
[ロードマップ](docs/roadmap.md)で章間の疑問を確認してください。

## Requirements

- Zig **0.17.0**。dev/masterや別versionのAPIを混ぜない
- 標準環境: **M2 MacBook Air → OrbStack → Arch Linux ARM64 (aarch64)**
- Linux x86_64実機や別VMでも学習可能。epoll/io_uring/strace実験はLinuxで実施
- strace、man、editor。nc/socatはsocket実験、perf等は任意

## Linux setup

macOSでOrbStackを導入後、Linux machineを作ります。
Arch対応とCLI形式は[対応distro](https://docs.orbstack.dev/machines/distros)と
[OrbStack commands](https://docs.orbstack.dev/machines/commands)で確認できます。

```sh
orb create arch zig-syscall-lab
orb -m zig-syscall-lab
uname -m
```

M2ではARM64環境を使い、unameがaarch64か確認します。以後のコマンドはLinux shell内で実行します。

```sh
sudo pacman -Syu
pacman -Si strace man-db man-pages neovim socat openbsd-netcat git
sudo pacman -S strace man-db man-pages neovim socat openbsd-netcat git
```

package名の一次資料、追加tool、Zigの導入は[Arch + OrbStack環境手順](docs/arch-orbstack.md)。
Archはrolling releaseです。[公開ARM packageのzig](https://archlinuxarm.org/packages/aarch64/zig)は確認時点で0.16.0-1なので、
**pacmanでzigを入れれば0.17.0になるとは仮定しません**。
[Zig公式0.17.0配布](https://ziglang.org/download/0.17.0/)のaarch64-linux版を利用し、`zig version`で0.17.0を確認します。

```sh
git clone https://github.com/moribit/zig-syscall-lab.git
cd zig-syscall-lab/01-file-descriptor
export EDITOR=nvim
touch main.zig
$EDITOR main.zig
```

コード編集、コンパイル、実行、straceを同じLinux環境で行うと、OS/architectureとpathの混乱を減らせます。
macOS editorを使う場合も、compileと観測はLinux shell内で行います。
io_uringの利用可否はkernel、policy、resource制限と返却errnoで確認してください。
VMのperf countersには制約もあります。[Linux I/O](docs/linux-io-overview.md)。

## How to study

1. READMEを読み、図・所有権・syscallの予想をnotes.mdへ書く。
2. main.zigを作る。
3. importとmainから自分でコードを書く。
4. `zig run main.zig`で実行する。
5. エラーを読む。
6. 修正して再実行する。
7. `zig build-exe main.zig`で観測用binaryを生成する。
8. Linuxで`strace ./main`を実行する。
9. 予想との差とREADMEの問いに答える。
10. 次章へ進む。

最初から正しいコードを書く必要はありません。コンパイラエラーも教材の一部です。
error union、optional、integer cast、pointer型、alignment、sliceのexpected/foundを読み、
stdlibの宣言と比較して修正します。これらのエラーを隠すhelperは提供しません。

## Zig CLIを使い分ける

普段の試行錯誤は、その章のディレクトリで実行します。

```sh
zig run main.zig
```

プログラム引数は`zig run main.zig -- 引数`で渡します。
compileだけを行い、後から実行するときは以下です。

```sh
zig build-exe main.zig
./main
```

通常の出力名はmainです。cat.zig/cp.zigなどを自分で作った場合はbinary名も変わります。
必要なら`-femit-bin=cat`のように明示できます。ZigのsourceはGit管理し、生成binaryは管理しません。

## How to use strace / perf

```sh
zig build-exe main.zig
strace -f -tt -T -o trace.log ./main
strace -f -c ./main
```

`zig run`自体をstraceするとcompiler・linker・学習対象programのsyscallが混ざります。
先にbinaryを作り、学習対象だけを観測してください。回数、返却値、fd、blocking地点を予想と比較します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat ./main
```

perfも生成binaryを対象にします。DebugとReleaseFastの違い、観測負荷、VM countersは16章で扱います。
詳しい読み方は[debugging](docs/debugging.md)。

## 自分のコードを履歴にする

学習後はmain.zig、必要になって作ったconnection.zig、notes.mdをそのままcommitして構いません。
初期状態はREADMEのみ、学習後は自作sourceと実験記録が加わり、repoが自分の学習履歴になります。
.gitignoreはmain等の生成binary、object、cache、trace/perfデータを除外し、.zig fileは除外しません。
入力fixtureや測定レポートを残すかは自分で決めます。自動検査の成功印より、manual experimentと観測を重視します。

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

[一次資料](docs/references.md)、[API source索引](docs/api-audit.md)、[用語集](docs/glossary.md)、
[改修後の確認記録](docs/verification.md)。各章でLinux man pagesと同梱stdlib sourceを読みます。
