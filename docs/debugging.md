# syscallを観察する

実装前に「fd・要求長・返却値・待機条件」の4列を書きます。実装後はLinuxで以下を使います。

```sh
strace -f -tt -T -o trace.log ./zig-out/bin/lab-07
strace -f -c ./zig-out/bin/lab-07
strace -f -e trace=network,read,write,close,epoll_ctl,epoll_wait ./zig-out/bin/lab-07
ss -tnp
ls -l /proc/<pid>/fd
pidstat -p <pid> 1
```

cat/cpには引数を付け、serverには別terminalのclientを接続します。最初はfilterなしで
初期化も観察し、次に対象syscallを絞ります。aarch64ではepoll_wait wrapperが
別のsyscall（epoll_pwait等）へ降りる場合があるため名前の一致だけで判断しません。
`unfinished/resumed`はthread間表示の分割です。`EAGAIN`はreadyでない状態、`EINTR`はsignal割込。
長い`-T`はkernel内滞在時間で、CPUを消費した時間とは限りません。

blocking実験はclient Aを無送信にしてBを送信。non-blocking実験は全clientをidleにしCPUを見る。
ET実験で永久待機しそうなら外部timeoutを用意します。traceは別runで取り、通常latency測定と混ぜません。
SIGPIPE、EOF、RST、half-closeは別々に試します。EOF後にもpending writeがある設計を説明してください。

```sh
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-07
/usr/bin/time -v ./zig-out/bin/lab-07
```

perfの権限・VM counters・kernel設定によって測れない項目はN/Aと理由を記録します。
macOSのdtruss等はLinux syscallと一致せず、この教材のLinux traceの代わりにはしません。

## 観測記録テンプレート

| 入力/環境 | 予想syscall/返却値 | 実測/回数/待機時間 | 差の理由 | 再実験 |
|---|---|---|---|---|
| 自分で記入 | | | | |

memory leakは終了時allocator検査と長時間RSSの両方、fd leakは/proc/pid/fdの増減で確認します。
短いI/Oを確実に検査するには偽backendから1 byte、EAGAIN、EINTR、EOFを注入するunit testも使います。
