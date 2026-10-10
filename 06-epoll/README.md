# Chapter 06: epoll Fundamentals

## この章で学ぶこと

interest list、ready list、LT/ET、IN/OUT/ERR/HUP。

## 前章とのつながり

pollの繰り返し登録とscanを分離します。

## 背景

epoll fdはkernelにinterest listを持ち、ready listからeventを返します。これはreadiness通知でありI/Oの完了ではありません。

## OS内部では何が起きているか

epoll instanceは登録済みinterestとreadyの管理を行います。socket bufferの状態変化が通知へつながり、返却eventを受けてuserspaceがI/Oを行います。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`epoll_create1, epoll_ctl, epoll_wait, read, write, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.epoll_create1/epoll_ctl/epoll_wait / epoll_event / EPOLL`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

pipeかsocketpairのread側をLTで登録。1 byteだけ読む実験、drainする実験、ETへ切替える実験を実装する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. create→ADD(IN)→入力3 byte→wait→1 byte read→再wait。LTの結果を記録後、ETで同じ操作をする。最後にEAGAINまでdrainする。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

再wait前に新しい書込をしない。LTとETで通知の違い、ERR/HUP時のbuffer残量を観察する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-06
strace -f -c ./zig-out/bin/lab-06
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

ETで1 readだけ／non-blockingを忘れる／data.fdだけをidentityにしてfd再利用を誤認。

## ヒント

tagged unionでeventの種類を、generation付きtokenでconnectionの世代を表せる。ABIのepoll_event layoutを手で変更しない。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

3 byte実験をLT/ETで説明し、idle timeout・HUP・DELのtraceを保存する。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

EPOLLONESHOTとrearm、dup fdとinterestの関係を調べる。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-06`も試します。

## 次章への問い

> ready通知をconnectionの状態遷移へどう結びつけますか？

## interestとreadyを分離する

```text
socket A ─┐
socket B ─┼── epoll interest list (ADD/MOD/DELで維持)
socket C ─┘             │ ready condition
                       ▼
                  ready list
                       │ epoll_wait()
                       ▼
                  ready events only
                       │
                アプリがread/write
```

`epoll_ctl`で何に関心があるかを登録し、`epoll_wait`で現在通知されるeventを受けます。
登録数と返却event数は別です。maxeventsは出力配列容量で、interest数ではありません。
「全処理がO(1)」とは言えません。返却eventのdispatch・データ転送・登録変更には仕事があります。

| flag | 何を試すか | 注意 |
|---|---|---|
| EPOLLIN | read/accept | EOFもreadで判定。EAGAINの可能性を処理 |
| EPOLLOUT | pending send | 通常readyなので常時登録はCPU浪費 |
| EPOLLERR | socket error確認 | 通常はSO_ERROR等で理由を調べ、cleanupを決める |
| EPOLLHUP | peer状態と残データ確認 | 未読byteを直ちに捨てない |
| EPOLLRDHUP | peerの送信側half-close | pending outputをどう扱うか決める |
| EPOLLET | edge-triggered指定 | listener acceptとclient read/writeを適切にdrain |

ERR/HUPはinterestに明示しなくても通知されます。event flagsは複数bitを同時に持ち得るので
if/elseで一種類だけ処理する設計を見直します。read結果とflagsを合わせてstateを決めます。

## LTからETへ進む実験表

read側はnon-blocking。書込側から3 byteだけ渡し、その後は新しい書込をしません。
2回目waitは短いtimeoutを指定し、永久待ちを防ぎます。

| 条件 | 1回目read | 2回目waitの予想 | 結果 |
|---|---|---|---|
| LT | 1 byte | 残量がreadyなので再通知され得る | 自分で記入 |
| ET | 1 byte | 未読だけを理由に再通知を期待しない | 自分で記入 |
| ET | EAGAINまで | 空なので新しい変化を待つ | 自分で記入 |

ETは「syscallが常に1回で済む」方式ではありません。read/acceptの複数回が必要です。
readyが消えるまでdrainする一方、長いhandlerが他接続を飢餓にしない設計も後で必要になります。

## event tokenと解放

DEL→close→state解放の責任を決め、同じevent batch内のstale eventへ備えます。
fdが再利用されるためfdだけでは古いeventと新connectionを区別できません。
slot index + generationをdataに入れる設計を紙で試してください。
open file descriptionとdupの関係はepoll(7)のQ&Aも読みます。
