# Zig 0.17.0 API source確認

確認日: 2026-10-10。`zig version`は`0.17.0`。
`zig env`の`std_dir`を基準に同梱sourceを読みました。確認環境はaarch64-macos。
Linux APIの実行検証とは区別してください。以下のlineはこの配布sourceでの位置です。

```sh
zig version
zig env
# zig envのstd_dirを調べ、その場所のIo.zigをeditorで開く
```

## raw I/O: wrapperとsyscallを区別

| API | source | 確認した契約 |
|---|---|---|
| std.posix.read(fd, []u8) | posix.zig:402 | ReadError!usize、INTRを内部retry、AGAIN→WouldBlock |
| std.posix.openat(dir_fd, path, flags, mode) | posix.zig:443 | OpenError!fd_t、INTRを内部retry |
| std.posix.poll([]pollfd, i32) | posix.zig:1005 | PollError!usize |
| linux.read(fd, ptr, count) / write | os/linux.zig:1716 / 1787 | usizeの生返却値。linux.errnoでdecode |
| linux.close(fd) | os/linux.zig:2030 | 生返却値。Linuxではclose失敗時もfd再利用に注意、無条件retryしない |
| linux.socket/bind/listen/accept4 | os/linux.zig:2799 / 2881 / 2888 / 2926 | 生syscall。pointer/length、network byte orderを明示 |
| linux.sendto/recvfrom | os/linux.zig:2895 / 2859 | send/recv相当の入口。nullable address等の宣言を確認 |
| linux.epoll_create1(flags) | os/linux.zig:3095 | usize生返却値 |
| linux.epoll_ctl(epfd, op, fd, ?*epoll_event) | os/linux.zig:3099 | ADD/MOD/DELとdata tokenを明示 |
| linux.epoll_wait(epfd, [*]epoll_event, maxevents, timeout) | os/linux.zig:3103 | usize、targetに応じて下位syscallが異なる |
| linux.io_uring_setup(entries, *params) | os/linux.zig:3193 | 生返却値、paramsの返却offsetを使う |
| linux.io_uring_enter(fd, submit, complete, flags, ?*sigset_t) | os/linux.zig:3197 | submit結果とCQE.resは別 |
| linux.mmap | os/linux.zig:1577 | address/length/prot/flags/fd/offset、alignmentとerrnoを確認 |

この版では従来の`std.posix.write/close/socket/epoll_*`を前提にしません。
Linux syscallを直に使う章は`std.os.linux`を読み、error変換も学習者が設計します。
Linux生syscall章はlibcを経由しない入口を読みます。自分のCLIでも必要性を調べずに-lcを加えないでください。

## ring wrapperの位置

`std.os.linux.IoUring`はliburingへの依存ではなくZigの実装です。
09章は自作setup/mmap/NOPが基本課題。10–11章も自作ringを延長するのが基本で、
wrapperは照合・追加比較に使えます。wrapperだけ使ってring学習を完了にしません。

- IoUring.zig:27 `init(entries: u16, flags: u32) !IoUring`、39 `init_params`
- 139 `get_sqe`、157 `submit`、164 `submit_and_wait`、279 `copy_cqes`、335 `cq_advance`
- 393 `read`、416 `write`、508 `accept`、633 `recv`、657 `send`、985 `cancel`
- 1505/1579: SQ/CQ structとmapping。`IORING_FEAT_SINGLE_MMAP`分岐も読む
- 139: SQ headのacquire load、221: SQ tailのrelease publish。
  CQにも対応するorderingが必要。`volatile`だけではthread/kernelとの順序を保証しない

CQEの`res`はsigned結果で、負ならerrno、0はopcodeにより成功またはEOF、正ならbyte数等です。
SQE/CQE layoutは`os/linux/io_uring.zig`とlinux.zigのexportを追います。

## Ioとconcurrency

| 宣言 | source | 正確な意味 |
|---|---|---|
| Io.userdata / vtable | Io.zig:22 | 明示的な実装依存。allocatorと同様に引数で渡せる |
| Io.Threaded | Io.zig:28 | threadを使い得るbackend |
| Io.Evented | Io.zig:31 | fiber対応時、Linux=Uring、BSD=Kqueue、Darwin=Dispatch。それ以外void |
| Threaded.init(allocator, options) | Io/Threaded.zig:1611 | Threadedを返す。async系利用時allocatorはthreadsafeである必要 |
| Threaded.deinit / io | Io/Threaded.zig:1716 / 1811 | backend lifetime内だけIoを使う |
| process.Init.io / gpa | process.zig:31 | mainへ渡される初期化済み依存 |
| Io.async(io, function, args) | Io.zig:2526 | Future(Result)。即時完了を許す。並行実行の強い保証なし |
| Io.concurrent(io, function, args) | Io.zig:2565 | ConcurrentError!Future(Result)、ConcurrencyUnavailableあり |
| Future(Result).await(io) | Io.zig:1319 | Resultを返す。旧言語await構文ではなくmethod |
| Future(Result).cancel(io) | Io.zig:1311 | 取消を要求し結果まで待つ。Resultを返す |
| Group.init/async/concurrent/await/cancel | Io.zig:1338–1427 | group全体で回収。taskはCancelable!voidへcoerce可能 |
| Io.sleep(io, Duration, Clock) | Io.zig:2599 | Cancelable!void、cancel pointの実験に使う |
| Thread.getCurrentId() | Thread.zig:279 | thread観測。completion順を保証するものではない |

API名を手掛かりに宣言を探し、呼出側の引数とerror処理を自分で組み立てます。

`Io.async`の単独Futureと`Group.async`の契約は同じではありません。
Groupのasync taskはawait/cancelまで実行されないこともあります。
`Future.cancel`は次のcancel pointでCanceledを通知します。取消要求は強制thread killではありません。
Canceledを無視すると取消を失うため、伝播または明示的なrecancel設計が必要です。
CPUだけの無限loopにcancel pointがなければcancelは速やかに終わる保証がありません。

`init.io`と明示Threadedを別実験にします。Eventedはtargetのfiber対応をsourceで確認した上で発展課題にします。
旧Zigの`async fn`や言語組込`await future`のサンプルをこの教材へ持ち込まないでください。

## allocationとcontrol flowの読み方

Zig言語のallocationは暗黙のGC任せではありません。ただしstdlibのbackendやasync操作は
渡されたallocatorを内部で使えます。「std.Ioを呼べばallocationが一切ない」とは解釈しません。
allocatorの供給元、backendの寿命、実際のallocation箇所をsourceで追います。
error unionのtry/catch、defer/errdeferは失敗時の所有権を明示するための道具です。

## 宣言を自分で探す

この索引のline番号は配布sourceの位置です。引数を埋めた実装例は掲載しません。
editorで各関数名を検索し、引数型、返却型、error setをメモします。
Linux man pageのC APIとstdlibの生syscall・wrapperを比較してください。
調べた宣言を使って自分のmain.zigへ1操作ずつ書き、コンパイラが指摘した型とsourceを照合します。
