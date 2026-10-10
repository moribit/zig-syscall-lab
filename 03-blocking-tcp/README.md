# Chapter 03: Blocking TCP

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

TCP byte stream、socket lifecycle、blocking。

## 前章とのつながり

ファイル転送のloopをTCPへ適用します。

## 背景

listen socketとaccepted socketは別fdです。acceptは接続、readは受信データを待ちます。TCPはmessage境界を保存しません。

## OS内部では何が起きているか

listen queueに接続が入りacceptで新しいfdが生まれます。受信queueが空ならblocking readのthreadを待機させ、データ到着で再開します。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`socket, bind, listen, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.socket/bind/listen/accept4/read/sendto`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux.zigと各architecture syscall実装`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 2 socket
man 2 bind
man 2 listen
man 2 accept
man 2 recv
man 2 send
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

127.0.0.1:9000で一度に1接続を処理するecho server。受信したbyteを順序どおり返す。

## 実装手順

1. main.zigにIPv4 loopback、port 9000を使う設定を手書きする。
2. socketを取得してbindする。sockaddr layoutとnetwork byte orderを確認する。
3. listenしたfdとacceptで得たfdを別変数で管理する。
4. 一つのclientをread→全量write→EOFまで処理し、closeしてからacceptへ戻る。
5. SIGPIPE、RST、途中失敗でserverを継続する方針を決める。
6. 2 terminalでclientを接続し、一方がidleの時の待ち箇所を観測する。

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

Terminal Aでserverを起動します。

```sh
zig run main.zig
```

Terminal BとCでそれぞれ接続します。

```sh
nc 127.0.0.1 9000
```

Bを無送信にし、Cで文字を送ります。Cのconnectとecho開始を区別し、B切断後の進捗を確認します。
半切断の実験は`printf 'hello\n' | nc -N 127.0.0.1 9000`で行えます。

## 観察ポイント

Aを無送信のまま接続しBを接続する。BのechoがA切断まで進まないことを確認する。
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

1 read = 1 messageと思う／listen fdへreadする／peer切断後のsendでSIGPIPE。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux.zigと各architecture syscall実装`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

C ABIのsockaddrはextern layout。sendtoのMSG.NOSIGNAL等でSIGPIPE方針を明示する。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

echo、binary転送、切断後の再接続を確認し、idle client中のblocking箇所をtraceに示せる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

backlogとアプリが処理可能な接続数の違いを調べる。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> 待つreadをやめると複数接続を進められますか？

## 待機の図

```text
client A → accept → read ← Aが送信するまで待つ → write
client B → kernelの待機queue … アプリはまだacceptへ戻らない
```

Bのconnect成功だけではBのecho処理開始を意味しません。
accept queue、アプリが所有するconnection、readの待機を区別します。
