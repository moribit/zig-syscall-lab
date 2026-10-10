# Chapter 13: Zig std.Io

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

## 実装課題

init.ioを受け取るfile readerを実装し、allocatorとioを引数に渡す関数へ分離。次にThreadedを明示生成し差を観察する。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. mainにstd.process.Init→io取得→関数へ引渡し→File/Dir API source確認→Threaded lifecycle比較。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

std.Ioを使っただけで全I/Oがio_uringになると予想せずtraceでbackendを判定する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-13
strace -f -c ./zig-out/bin/lab-13
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

旧std.fs APIをそのまま使う／Ioをglobal化／Threadedをio利用中にdeinit。

## ヒント

fn foo(allocator: std.mem.Allocator, io: std.Io) !void の依存を考える。allocation/control flowはsourceとtraceから追う。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

DI関数とcat仕様が動き、自作loopとの責務対応表ができる。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

Eventedはfiber対応とOS条件でvoidにもなる。LinuxではUring aliasであることをsourceで確認し、利用可能なら比較する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-13`も試します。

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
