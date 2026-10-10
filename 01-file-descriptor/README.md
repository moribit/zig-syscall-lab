# Chapter 01: File Descriptor

## この章で学ぶこと

プロセスとfd table、0/1/2、open/close/read/write。

## 前章とのつながり

開始章です。端末とファイルを同じ整数で扱える理由を考えます。

## 背景

fdはプロセス内の索引です。kernelのopen file descriptionに接続され、offsetやstatus flagsはそこに属します。fd番号は永続的なidentityではありません。

## OS内部では何が起きているか

fd tableはprocessの索引で、kernel objectの実体ではありません。closeするとslotが空き、次のopenで再利用されます。標準fdも通常のdescriptorです。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`openat, read, write, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.posix.fd_t / openat / read、std.os.linux.write / close`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## 実装課題

stdoutへ直接writeし、stdinを一度readする。hello.txtを開き、fd番号をstderrへ表示する。さらに3ファイルを同時に開く。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. 出力hello\n→stdin入力→ファイルを開く→fdを記録→逆順にcloseする。標準fdをcloseした別実験で番号の再利用を確認する。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

stdoutをファイルへredirectした場合と端末の場合でfd=1の参照先を比較する。/proc/<pid>/fdを調べる。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-01
strace -f -c ./zig-out/bin/lab-01
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

fd=3が必ず最初になると仮定する／closeしたfdを使う。

## ヒント

deferは取得成功直後に置く。複数取得の途中失敗にはerrdeferで所有権を整理する。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

端末・redirect・複数openの3つの図とtraceを提出する。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

dupしたfdでoffsetの共有を実験する。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-01`も試します。

## 次章への問い

> read/writeは1回で全データを転送するのでしょうか？

## fdの図を完成させる

```text
Processのfd table (kernel管理)       Kernel objects
fd番号をuserspaceが指定              open file descriptions
0 ───────────────────────────────> terminal stdin
1 ───────────────────────────────> terminal stdout
2 ───────────────────────────────> terminal stderr
3 ───────────────────────────────> hello.txt (offset / status flags)
```

予想: 0/1/2が開いている場合、次のopenでどの整数が返るか？
実験: 3ファイルを開いた後、中間のfdだけcloseしてもう1ファイルを開きます。
確認: 「fd番号」「ファイル名」「offset」「close責任」を別々に書きます。
stdoutへ`hello\n`、stdinで得たbyteをstdoutへ返すところから始めてください。
診断情報はstderrへ出すと、stdout redirectの実験が汚れません。
