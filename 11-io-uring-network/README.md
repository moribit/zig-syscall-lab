# Chapter 11: io_uring Network

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

accept/recv/send completion、operation lifecycle。

## 前章とのつながり

fileのcompletion管理をsocketへ応用します。

## 背景

recv完了までbufferはkernelから参照されます。closeやcancel要求だけでoperationの完了を見なしてはいけません。

## OS内部では何が起きているか

accept completionは新client fd、recv/send completionは転送結果です。operationはconnection stateより長く残り得るため、close後のCQEも回収計画が必要です。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`socket, bind, listen, io_uring_enter, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.IoUring.accept/recv/send/cancel（確認用）`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux/IoUring.zigのaccept/recv/send/cancel`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 7 io_uring
man 2 accept
man 2 recv
man 2 send
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

単発accept・recv・sendのecho。最初は1接続、次に複数接続とoperation tokenを導入する。

## 実装手順

1. main.zigへsocket/bind/listenと自作ringを手書きする。
2. 単発acceptをsubmitし、CQEから新しいclient fdを得る。
3. recv完了までbufferを保持し、そのbyteをsendへ渡す。
4. partial sendの残量を再要求してから次のrecvへ進む。
5. connection ID、世代、operation種をtokenとして設計する。
6. 複数接続へ広げ、切断・cancelと遅れて来るcompletionのcleanupを確かめる。

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

Terminal Aで`zig run main.zig`、別terminalで`nc 127.0.0.1 9000`を複数起動。
idle、echo、half-close、再接続を試します。転送中にclientを切断し、残ったoperationのcompletionを回収するまで
bufferを解放しないことをlogとownership図で確かめます。

## 観察ポイント

socket read/writeがtraceに出なくてもoperationはkernel内で行われることを説明する。
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

CQEをfdだけで識別／同一bufferへ複数recv／cancel完了と対象operation完了を混同。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux/IoUring.zigのaccept/recv/send/cancel`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

connection ID、世代、operation種をuser_dataに符号化する。pointerを使う場合はalignmentと寿命を文書化する。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

複数echoと切断時のin-flight回収を確認し、partial sendとcancelの所有権を説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

multishot acceptをfeature probe後に試し、CQE F_MOREと最終完了の意味を調べる。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> 自作loopの責務をstd.Ioはどう表しますか？ 次は13章です。
