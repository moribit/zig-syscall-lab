# 一次資料

Zigは0.17.0の同梱sourceを基準にします。masterのsourceを混ぜません。

- [Zig 0.17.0配布・release source](https://ziglang.org/download/0.17.0/)
- [Zig 0.17.0 language reference](https://ziglang.org/documentation/0.17.0/)
- [Zig 0.17.0 std documentation](https://ziglang.org/documentation/0.17.0/std/)
- [Zig stdlib tag source](https://codeberg.org/ziglang/zig/src/tag/0.17.0/lib/std)
- [Linux man-pages project](https://www.kernel.org/doc/man-pages/)
- [read(2)](https://man7.org/linux/man-pages/man2/read.2.html)、[write(2)](https://man7.org/linux/man-pages/man2/write.2.html)、[open(2)](https://man7.org/linux/man-pages/man2/open.2.html)、[close(2)](https://man7.org/linux/man-pages/man2/close.2.html)
- [socket(2)](https://man7.org/linux/man-pages/man2/socket.2.html)、[accept(2)](https://man7.org/linux/man-pages/man2/accept.2.html)、[poll(2)](https://man7.org/linux/man-pages/man2/poll.2.html)
- [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html)、[epoll_ctl(2)](https://man7.org/linux/man-pages/man2/epoll_ctl.2.html)、[epoll_wait(2)](https://man7.org/linux/man-pages/man2/epoll_wait.2.html)
- [io_uring(7)](https://man7.org/linux/man-pages/man7/io_uring.7.html)、[io_uring_setup(2)](https://man7.org/linux/man-pages/man2/io_uring_setup.2.html)、[io_uring_enter(2)](https://man7.org/linux/man-pages/man2/io_uring_enter.2.html)
- [kernel io_uring source/documentation](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/Documentation/io_uring)
- [kernel memory barriers](https://www.kernel.org/doc/html/latest/core-api/wrappers/memory-barriers.html)
- [liburing man source](https://git.kernel.dk/cgit/liburing/tree/man)（概念と契約の参考のみ。リンク・依存・実装利用はしない）

API照合のファイルと宣言は[確認ノート](api-audit.md)。man pageのkernel feature記述と手元kernelの対応を比べます。
