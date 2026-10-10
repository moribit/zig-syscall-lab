# syscallを観察する

実装前に「fd・要求長・返却値・待機条件」の4列を書きます。普段はzig run main.zigで修正を繰り返します。
観測時はLinuxでzig build-exe main.zigを使い、生成binaryだけを対象にします。
zig runをtraceするとcompiler/linkerのsyscallも混ざるためです。

```sh
zig build-exe main.zig
strace -f -tt -T -o trace.log ./main
strace -f -c ./main
strace -f -e trace=network,read,write,close,epoll_ctl,epoll_wait ./main
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
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
/usr/bin/time -v ./main
```

perfの権限・VM counters・kernel設定によって測れない項目はN/Aと理由を記録します。
macOSのdtruss等はLinux syscallと一致せず、この教材のLinux traceの代わりにはしません。

## 観測記録テンプレート

| 入力/環境 | 予想syscall/返却値 | 実測/回数/待機時間 | 差の理由 | 再実験 |
|---|---|---|---|---|
| 自分で記入 | | | | |

memory leakは終了時allocator検査と長時間RSSの両方、fd leakは/proc/pid/fdの増減で確認します。
短いI/Oが自然に起きない場合、実験用に1 byteずつ進める経路や失敗注入を自分で書いても構いません。
先にhelperを作るのでなく、正常系を理解してから境界状態を紙とlogで検証します。

コンパイラエラーではexpected/found、sliceとpointer、integer cast、alignment、error unionとoptionalを読みます。
エラーを隠すhelperは使わず、stdlib sourceの宣言と照合して自分のmain.zigを直します。
