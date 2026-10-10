# Chapter 09: io_uring Fundamentals

## この章で作るもの

自分で以下のファイルを作成します。

```text
main.zig
```

この教材からソースコードは提供しません。 単一fileのままSQ/CQとmappingを見える形で扱い、helperへの分離は後で行います。

## この章で学ぶこと

SQ/CQ、SQE/CQE、mmap、submission/completion。

## 前章とのつながり

08→12のevent loopを終え、readiness以外のモデルへ進みます。

## 背景

userspaceとkernelがringを共有します。SQに要求をpublishしCQで結果を回収します。submit成功とoperation成功は別です。

## OS内部では何が起きているか

setupはring fdとlayout情報を返し、mmapで共有領域をuserspaceへ見せます。kernelがSQ要求を取り、operation結果をCQへpublishします。
アプリの状態とkernelの状態を別に描き、境界を越える矢印を記入します。

## 今回使うsystem call

`io_uring_setup, mmap, io_uring_enter, munmap, close`。traceの名前はarchitectureやwrapperにより異なる場合があります。

## Zigからどう見えるか

`std.os.linux.io_uring_* / io_uring_params / io_uring_sqe / io_uring_cqe`。正確な宣言は[API確認ノート](../docs/api-audit.md)とZig 0.17.0同梱sourceを参照。
生`std.os.linux`の返却値はerror unionではありません。`linux.errno(rc)`で成功を判定してからfd/長さへ変換します。

## stdlibを読む

`zig version`が0.17.0であることを確認し、`zig env`のstd_dirをeditorで開きます。
今回読むsource: `os/linux.zig、os/linux/io_uring.zig、os/linux/IoUring.zig`。
関数の型、error set、Linux固有か、libcを経由するか、syscallへどう降りるかを調べてください。
宣言の引数を教材から埋めず、pointer/slice/alignmentをsourceから判断します。
[API確認ノート](../docs/api-audit.md)はsourceを探す索引です。

## man pageを読む

実装前にLinuxで以下を読みます。

```sh
man 7 io_uring
man 2 io_uring_setup
man 2 io_uring_enter
man 2 mmap
```

戻り値、0の意味、失敗時のerrno、EINTR、短い転送または待機条件を確認します。
manのC APIの-1/errnoとZig生syscallの返却値を混同しないでください。
章固有のflags・resource寿命も確認し、sourceのwrapperが何を変換するか説明します。
ページが未導入なら[一次資料](../docs/references.md)のmanリンクも参照してください。

## 実装課題

liburingなしでraw setup/mmapからNOPを1件送る。user_data=42のCQEを回収し、ring headを進める。

## 実装手順

1. main.zig一つでparamsとmapping、SQ/CQのpointerが見えるように書く。
2. paramsを初期化しio_uring_setupの成功/errnoを区別する。
3. 返却offsetから必要長を計算し、SINGLE_MMAPの分岐とSQE別mappingを実装する。
4. NOPのSQEを準備し、SQ arrayへindexを入れる。
5. entry初期化後にtailをrelease publishし、enterでsubmitする。
6. CQ tailをacquireで読み、user_data=42とres=0を確認する。
7. CQ headを進め、全mappingとring fdを解放する。
8. capacity=4の紙上ringで満杯とu32 wraparoundを検討する。

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

NOPのuser_data、res、head/tailをstderrへ記録して1件の進捗を追います。
利用不可のkernelではsetupのerrnoと環境条件を記録します。
紙上ringで空・満杯・wraparoundを確認後、容量を小さくして複数NOPをsubmitします。
CQEを消費しない場合の状態を観察し、上書きを防ぐ条件を説明します。

## 観察ポイント

setup返却値・SQ/CQ offset・entries/mask・head/tailを記録。CQEを消費しない場合のqueue状態を観察する。
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

tailだけ進める／CQE.resの負errnoをusizeにcast／volatileだけで順序保証／bufferを完了前に解放。

## ヒント

### Hint 1

まず上のman pageで操作の契約を調べ、1 fd・1 byte・1 operationへ縮小します。

<details>
<summary>Hint 2</summary>

調べるsource: `os/linux.zig、os/linux/io_uring.zig、os/linux/IoUring.zig`。API名は「Zigからどう見えるか」を参照し、宣言を探します。

</details>

<details>
<summary>Hint 3</summary>

extern/packed ABIはstdlib定義を使う。alignmentを保証する。volatileはatomicの代わりではない。acquire/releaseの対応を説明する。
関数シグネチャと成功/失敗時の状態をsourceで確認し、自分の所有権の図と照合してください。

</details>

## 完了条件

NOPのuser_data=42とres=0を確認し、満杯・wraparound・mapping解放の根拠を説明できる。
コードとnotes.mdへ入力・予想・実測・差の理由を残します。コンパイル成功だけを学習完了にはしません。

## 発展課題

stdlib IoUringの実装と自作mappingを比較。SQPOLLは追加実験に留める。
必要なら別runで生成binaryを測定します。

```sh
zig build-exe -O ReleaseFast main.zig
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./main
```

## 次章への問い

> 複数のreadを送ると、完了順はsubmission順でしょうか？

## まず図を理解する

```text
Application                          Kernel
    SQ (要求)
 ┌────────────┐    publish tail
 │ read fd=3  │ ───────────────────> consume SQ / execute I/O
 │ read fd=4  │   io_uring_enter             │
 │ accept     │                             ▼
 └────────────┘                       publish CQ tail
    CQ (結果)                               │
 ┌────────────┐                             │
 │ done #1    │ <───────────────────────────┘
 │ done #2    │  acquire tail / read CQE / advance head
 └────────────┘
```

SQ ring arrayはSQEそのものではなくSQE配列へのindexを持ちます。
SQEにはopcode・fd・address・length・offset・user_dataを設定します。
CQEはuser_dataで要求へ対応し、resとflagsで結果を解釈します。順序はsubmission順とは限りません。

## mappingの設計課題

1. `io_uring_params`のSQ/CQ offsetsとentriesを返却値から読む。
2. SQ ringサイズは`array offset + sq_entries * sizeof(u32)`、CQは`cqes offset + cq_entries * sizeof(CQE)`を基準に計算する。
3. `IORING_FEAT_SINGLE_MMAP`ならSQ/CQ共有mappingの最大必要長を使う。そうでなければ別々にmapする。
4. SQE配列を別offsetでmapする。page alignment、MAP flags、cleanup順をsourceで照合する。
5. head/tail/entries/mask/array/CQEのpointerをmappingから作る。返却offsetをhardcodeしない。

最初はSQPOLL・IOPOLL・registered buffer・multishotを使いません。NOPで転送bufferの複雑さを除きます。
setupが成功してもopcodeが利用可能とは限りません。kernel featureとprobeを区別します。

## ringの不変条件を実験する

- indexは`counter & mask`。counter自体をmaskした値だけで保持しない。
- occupancyはwrapping subtraction。満杯時に未消費entryを上書きしない。
- SQEとarrayを書いた後、releaseでtailを公開。kernel headを読む側はacquire。
- CQ tailをacquireで読み、CQEを処理した後にheadを公開する。
- `io_uring_enter`が一部だけsubmitした時は残り要求を失わない。
- CQE.resのoperation失敗はsetup/enterの失敗とは別経路。
- cancelやcloseを要求しても、kernelが参照する領域を早く解放しない。

紙上queue（capacity=4）で0件・4件・満杯・head/tail wraparoundを先に検証します。
atomicsは「高速化の飾り」ではなくkernelに初期化済みentryを見せる契約です。
