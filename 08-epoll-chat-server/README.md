# Chapter 08: epoll Chat Server

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

backpressure、slow client、broadcast、lifecycle。

## 前章とのつながり

echoから他connectionへの出力へ広げます。

## 背景

送信先ごとに進捗が異なります。無制限queueは遅いclientによってメモリを使い尽くします。TCP flow controlだけではアプリqueueを制限できません。

## OS内部では何が起きているか

kernel送信queueが詰まるとsendは短くなるかEAGAINになります。userspace queueを無制限にするとkernelのflow controlだけではmemory増加を防げません。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`epoll_wait, epoll_ctl, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`allocator、optional、tagged unionとLinux epoll`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux.zigのsendtoとepoll_ctl`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 7 epoll
man 2 send
man 7 tcp
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

newline区切り、最大4096 byteのmessageを他clientだけへbroadcast。未送信queue上限64KiBで遅いclientを切断する。

## 実装手順

1. echoの経験からmain.zigへnewline frameの組立を自分で書く。
2. 最大frame4096 byte、per-client未送信queue64KiBと仕様を決める。
3. 送信者以外のconnectionへbroadcastし、receiverごとに送信進捗を持つ。
4. queueが空でない間だけOUTを登録する。
5. queue上限を超えるslow clientだけを切断する。
6. 受信fragment、切断中のbroadcast、message所有権を観測する。
7. 責務の重複が見えてからfile分割を検討する。

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

Terminal Aで`zig run main.zig`、別の3 terminalで`nc 127.0.0.1 9000`。
一人の入力が他二人だけへ届くかを確認します。入力を数回に分け、newlineまでframeが完成しないことを確認します。
次に受信を読まないclientを用意し、broadcastを続けます。
一時的にqueue上限を小さくし、slow clientだけが切断され、他clientとRSSが安定するか記録します。
単なるidle senderはslow receiverの再現にはならないので、receiverの読取を停止してください。

## 観察ポイント

1 receiverを読まないままbroadcastを続ける。RSSとqueue長を測り、他clientの進捗を確認する。
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

送信者bufferを共有したまま上書き／切断中に配列をiterate／無制限buffer。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux.zigのsendtoとepoll_ctl`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

共有messageを使うなら参照数、copyなら各queueの所有権と費用を示す。まず明確なcopy方式を選んでもよい。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

3 clientのbroadcast、分割frame、slow client切断を確認し、queue上限と所有権を説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

high/low watermarkで入力をpause/resumeする別方針を比較する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> dispatchの共通部分をOS APIから分離できますか？ 次は12章です。

## ファイル分割を考える

ここまで単一ファイルで実装しました。分割した方が良い責務はありますか？
connection.zigやevent_loop.zigを自分で作る場合も、まず重複とownershipの境界を説明してください。
最初からSocketやConnectionManagerのhelperを置かず、ベタ書き→理解→重複→抽象化の順に進めます。
