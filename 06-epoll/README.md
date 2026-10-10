# Chapter 06: epoll Fundamentals

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

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

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux.zigのepoll関数・epoll_event`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 7 epoll
man 2 epoll_create
man 2 epoll_ctl
man 2 epoll_wait
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

pipeかsocketpairのread側をLTで登録。1 byteだけ読む実験、drainする実験、ETへ切替える実験を実装する。

## 実装手順

1. non-blockingなpipeかsocketpairを作り、read側へ3 byte渡す。
2. epoll_create1でepoll fdを取得し、epoll_ctlのADDでINを登録する。
3. LTでepoll_waitし、1 byteだけreadする。
4. 短いtimeoutで再waitし、残り2 byteとの関係を記録する。
5. ETへ変更し、新規writeなしで同じ操作を繰り返す。
6. EAGAINまでdrainする方式へ変更し、HUP/ERRと残データを調べる。
7. DEL、close、event tokenの寿命を順に確認する。

## 実行

前章と同様に、自分でmain.zigを作成してください。まず単一fileで書きます。

```sh
touch main.zig
$EDITOR main.zig
zig run main.zig
```

$EDITORは事前に設定したeditor名です（例: nvim）。コンパイラエラーも教材の一部です。
型、error union、optional、integer cast、pointer、alignment、sliceの要求を読み、修正して再実行します。
引数がある課題は`zig run main.zig -- 引数`で渡します。

## 手動で確認

pipe/socketpairへ3 byteを一度だけ渡し、最初は1 byteだけreadします。
再waitには短いtimeoutを使い、新しいwriteなしでLT/ETを比較します。
read側を閉じる場合とwrite側を閉じる場合を分けてERR/HUPとread結果を記録します。

## 観察ポイント

再wait前に新しい書込をしない。LTとETで通知の違い、ERR/HUP時のbuffer残量を観察する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

普段は`zig run main.zig`、観察時は先にbinaryを生成します。

```sh
zig build-exe main.zig
strace -f -tt -T -o trace.log ./main
strace -f -c ./main
```

引数がある課題は`./main`の後に付けます。serverは別terminalでclientを接続し、終了後の集計を読みます。
`zig run`自体をtraceするとcompilerとlinkerのsyscallが混ざるため、学習対象binaryだけを観測します。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
program初期化と自分の処理の違いも調べます。[観察手順](../docs/debugging.md)。

## よくある失敗

ETで1 readだけ／non-blockingを忘れる／data.fdだけをidentityにしてfd再利用を誤認。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux.zigのepoll関数・epoll_event`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

tagged unionでeventの種類を、generation付きtokenでconnectionの世代を表せる。ABIのepoll_event layoutを手で変更しない。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

3 byte実験をLT/ETで説明し、idle timeout・HUP・DELのtraceを記録できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

EPOLLONESHOTとrearm、dup fdとinterestの関係を調べる。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

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
