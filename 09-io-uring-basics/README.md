# Chapter 09: io_uring Fundamentals

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

## 実装課題

liburingなしでraw setup/mmapからNOPを1件送る。user_data=42のCQEを回収し、ring headを進める。

## 実装手順

1. 入出力契約と所有権を紙に書き、syscall順を予想する。
2. paramsを初期化→setup→返却offsetからmap→SQE準備→SQ array→tail publish→enter→CQ acquire→res確認→head更新→unmap。
3. 正常系を動かした後、短い転送・切断・失敗を加える。
4. `test/contract.zig`のTODOへ自分の状態管理のunit testを追加する。

starterは未実装です。`implemented`をtrueにするだけでは完了ではありません。

## 観察ポイント

setup返却値・SQ/CQ offset・entries/mask・head/tailを記録。CQEを消費しない場合のqueue状態を観察する。
予想・実測・差の理由を`notes.md`へ記録します。待ったsyscall、回数、fd、返却値を必ず含めます。

## straceで確認

章ディレクトリでLinux上から実行します。

```sh
zig build
strace -f -tt -T -o trace.log ./zig-out/bin/lab-09
strace -f -c ./zig-out/bin/lab-09
```

serverは別terminalでclientを接続し、終了後の集計を読みます。cat/cp章はCLI引数を末尾に付けます。
どのsyscallが呼ばれたか、何回か、どこでblockingしたかを予想と比較してください。
ランタイム初期化のsyscallと自分の処理を区別します。[観察手順](../docs/debugging.md)。

## よくある失敗

tailだけ進める／CQE.resの負errnoをusizeにcast／volatileだけで順序保証／bufferを完了前に解放。

## ヒント

extern/packed ABIはstdlib定義を使う。alignmentを保証する。volatileはatomicの代わりではない。acquire/releaseの対応を説明する。
答えのloopは用意していません。困ったら1 fd、1 byte、1 operationに縮小します。

## 完了条件

NOPのuser_dataとres=0を確認し、満杯・wraparound・cleanupの試験を追加する。
`zig build test`は未実装時SKIP。実装後はSKIPを残さず自作unit testと`test/README.md`の挙動検査を実行します。

## 発展課題

stdlib IoUringの実装と自作mappingを比較。SQPOLLは追加実験に留める。
別runで`perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions ./zig-out/bin/lab-09`も試します。

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

## ringの不変条件をtestする

- indexは`counter & mask`。counter自体をmaskした値だけで保持しない。
- occupancyはwrapping subtraction。満杯時に未消費entryを上書きしない。
- SQEとarrayを書いた後、releaseでtailを公開。kernel headを読む側はacquire。
- CQ tailをacquireで読み、CQEを処理した後にheadを公開する。
- `io_uring_enter`が一部だけsubmitした時は残り要求を失わない。
- CQE.resのoperation失敗はsetup/enterの失敗とは別経路。
- cancelやcloseを要求しても、kernelが参照する領域を早く解放しない。

紙上queue（capacity=4）で0件・4件・満杯・head/tail wraparoundを先に検証します。
atomicsは「高速化の飾り」ではなくkernelに初期化済みentryを見せる契約です。
