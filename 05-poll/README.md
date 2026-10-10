# Chapter 05: poll

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

pollfd、POLLIN/POLLOUT、O(n) scan。

## 前章とのつながり

busy loopの待機をkernelへ任せます。

## 背景

pollは毎回渡された配列を調べ、reventsを更新します。readyでも次のreadが必ず成功する保証はありません。

## OS内部では何が起きているか

kernelはpollへ渡されたfd配列を調べ、必要ならwait queueへ待機者を結び付けます。復帰後もアプリが全reventsをscanする仕事が残ります。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`poll, accept4, read, sendto, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.posix.poll / pollfd / POLL`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `posix.zigのpollとpollfd`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 2 poll
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

non-blockingな複数client echo。pending writeがあるfdだけPOLLOUTを要求する。

## 実装手順

1. pollfd配列を作り、listenerとclientのfdを追加する。
2. eventsとreventsを区別し、pollのtimeoutを選ぶ。
3. readyなlistenerからacceptし、clientからread/writeする。
4. pending outputがある時だけPOLLOUTを要求する。
5. HUP/ERR/NVALとEOFを分けてslotを更新する。
6. 接続数を増やし配列長、ready数、userspace scanの負荷を記録する。

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

Terminal Aで`zig run main.zig`、Terminal B/Cで`nc 127.0.0.1 9000`。
BをidleにしてCのechoが進むことを確認します。切断後に新しいclientを接続し、slotの対応も確認します。

## 観察ポイント

1/100/1000 idle接続で配列長とready数、処理時間を記録する。
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

eventsとreventsを混同／POLLHUPだけで残データを捨てる／常時POLLOUT。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `posix.zigのpollとpollfd`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

ERR/HUP/NVALも調べる。通常fileはいつもreadyで、disk I/Oの待ちをpollで解消できるとは限らない。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

idle接続が他clientを妨げず、idle時にpollで待ち、pending outputだけにPOLLOUTを登録する。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

swap-removeによるslot変更時のfdとstate対応を検証する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> 毎回全fd配列を渡す必要はありますか？
