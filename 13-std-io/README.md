# Chapter 13: Zig std.Io

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。

## この章で学ぶこと

Io依存注入、Threaded、init.io、backend。

## 前章とのつながり

11章までの自作runtimeと標準abstractionを比較します。

## 背景

Ioはuserdataとvtableを持ち、I/Oとconcurrencyをbackendへ委譲します。ThreadedはOSのblocking operationとthreadを使い得ます。

## OS内部では何が起きているか

Ioはuserspaceのinterfaceです。選択backendがsyscallやworkerを使い、同じIo操作でもkernelへ到達する経路が変わります。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`openat, read, write, futex（backendと操作により異なる）`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.process.Init.io、std.Io.Threaded.init/deinit/io、std.Io.File`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `Io.zig、process.zig、Io/Threaded.zig、Io/File.zig`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 2 read
man 2 write
man 2 futex
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

init.ioを受け取るfile readerを実装し、allocatorとioを引数に渡す関数へ分離。次にThreadedを明示生成し差を観察する。

## 実装手順

1. mainの引数にstd.process.Initを受け取る設計をsourceから調べる。
2. init.ioを取得し、file操作を自分で書く。
3. allocatorとioを引数へ渡す関数を設計する。
4. cat PATHを実装し、自作raw版と同じbyteになるか比較する。
5. Threadedを明示init/deinitする別実験を行い、io利用期間をbackend寿命内に収める。
6. vtableからOS backendへ追い、traceで実際の待機経路を確認する。

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

CLIをcat PATHとして自分で定義します。

```sh
printf 'std Io\n' > input.txt
zig run main.zig -- cat input.txt
zig build-exe main.zig
./main cat input.txt > output.txt
cmp input.txt output.txt
```

init.ioと明示Threadedの二つの実験で、同じfile内容と異なるsyscall経路を比べます。

## 観察ポイント

std.Ioを使っただけで全I/Oがio_uringになると予想せずtraceでbackendを判定する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

普段は`zig run main.zig`、観察時は先にbinaryを生成します。

```sh
zig build-exe main.zig
strace -f -tt -T -o trace.log ./main cat input.txt
strace -f -c ./main cat input.txt
```

引数がある課題は`./main`の後に付けます。serverは別terminalでclientを接続し、終了後の集計を読みます。
`zig run`自体をtraceするとcompilerとlinkerのsyscallが混ざるため、学習対象binaryだけを観測します。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
program初期化と自分の処理の違いも調べます。[観察手順](../docs/debugging.md)。

## よくある失敗

旧std.fs APIをそのまま使う／Ioをglobal化／Threadedをio利用中にdeinit。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `Io.zig、process.zig、Io/Threaded.zig、Io/File.zig`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

fn foo(allocator: std.mem.Allocator, io: std.Io) !void の依存を考える。allocation/control flowはsourceとtraceから追う。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

catのbyteが一致し、Io/allocator依存注入とThreadedの寿命を自作loopと比較できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

Eventedはfiber対応とOS条件でvoidにもなる。LinuxではUring aliasであることをsourceで確認し、利用可能なら比較する。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> asyncは実際に同時進行することを保証しますか？

## abstractionの位置

```text
Application (allocator / Io を引数で渡す)
                  │
               std.Io
          userdata + vtable
                  │
        ┌─────────┴─────────┐
     Threaded          Evented (target条件付き)
   blocking OS API      Linux: Uring
   + thread等           Darwin: Dispatch / BSD: Kqueue
        └─────────┬─────────┘
              OS backend
```

std.Ioは単一の実行方式の名前ではありません。allocatorのように依存を明示することで
同じlogicの動作・失敗・待機方式を変えられます。自分のregister/wait/dispatchが
どのvtable methodやtask管理へ対応するか表を書いてください。
init.ioのbackendを推測で決めず、起動sourceとtraceを照合します。
