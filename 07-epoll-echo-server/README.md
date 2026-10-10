# Chapter 07: epoll Echo Server

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

connection state、pending write、event dispatch。

## 前章とのつながり

06の実験をserverのloopへ育てます。

## 背景

1回のeventで複数connectionをdispatchします。readinessは後続操作の成功保証ではなく、EAGAINまでの進捗機会です。

## OS内部では何が起きているか

各socketには独立した送受信queueがあります。epollが複数ready eventをまとめても、userspace側のconnection stateと未送信offsetは自動管理されません。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`epoll_wait, epoll_ctl, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linuxのepoll/socket API、allocator`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux.zigのepoll/socket API`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 7 epoll
man 2 accept
man 2 read
man 2 send
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

connectionにfd・世代・受信領域・送信領域・送信済みoffsetを設計する。全clientをnon-blocking echoする。

## 実装手順

1. 最初はmain.zigに全処理を直書きし、listenerをepollへ登録する。
2. connectionごとにfd、世代、buffer、pending byteと送信offsetを設計する。
3. epoll_waitで返るeventを順にdispatchする。
4. listenerはaccept、clientはreadをEAGAINまで進める。
5. partial sendの残量を保持し、必要な間だけOUTを登録する。
6. EOF、error、stale tokenとcleanupを別々に試す。
7. 単一の長いhandlerで他clientを飢餓にしないbudgetを考える。

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

Terminal Aで`zig run main.zig`、別terminalで`nc 127.0.0.1 9000`を複数起動します。
idle clientを残して他clientのechoを確認します。

```sh
printf 'fragment\n' | nc -N 127.0.0.1 9000
```

binary転送も生成binaryへ接続して確認します。

```sh
dd if=/dev/urandom of=input.bin bs=4096 count=16
socat - TCP:127.0.0.1:9000 < input.bin > output.bin
cmp input.bin output.bin
```

長時間の接続・切断でfd数が増え続けないか確認します。

## 観察ポイント

slow receiverでOUTが必要な間だけ登録されるか。連続切断でfdが再利用されるか。
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

event batch内の古いpointerを使う／buffer移動後のpointer保持／二重close。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux.zigのepoll/socket API`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

allocationの所有者とpointerの有効期限を図にする。malloc相当はallocatorを明示して行う。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

複数clientのecho、half-close、再接続、OUT切替を確認し、fd数が増え続けない。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

dispatchの公平性をbyte数または操作数budgetで制限する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> broadcastで送信量が増えたら遅いclientをどう扱いますか？
