# 単一ファイル教材への改修確認

確認日: 2026-10-10。教材の初期状態を対象にした文書・構造監査です。
17章の構成・必須導線・ヒント段階・local link・code fenceを監査し、全て成功しました。
生成物のignoreと自作Zig sourceがignoreされないこと、差分の空白検査も確認済みです。
学習者がこれから書くprogramのLinux動作検証とは区別します。

| 確認項目 | 改修後の状態 |
|---|---|
| root / chapterのbuild定義 | すべて削除 |
| 章内の提供Zig source | 0件。16章とcapstoneはREADMEのみ |
| 自動test・API probe・配布helper | 削除。検証内容は手動実験としてREADMEへ記載 |
| 旧project構成への実行指示 | 削除。main.zigを自分で作る方式へ統一 |
| 基本CLI | 全章にtouch / editor / zig run main.zig |
| syscall観測 | compile-onlyのzig build-exe後、strace ./main |
| perf | ReleaseFastの生成binaryを対象 |
| ヒント | 全章にHint 1、details内のHint 2/3。完成コードなし |
| 一次資料 | 全章にstdlib sourceとLinux man pageの読解課題 |
| file分割 | chat/event loop以後に学習者が判断 |
| 標準環境 | M2 + OrbStack + Arch Linux ARM64、package名は一次資料で確認 |
| Git管理 | sourceは管理可能。binary/object/cache/trace/perfはignore |

旧Zig APIの混入を避けるため、同梱Zig 0.17.0 sourceのread/openat/poll、Linux epoll/eventfd/io_uring、
Ioのasync/concurrent/Group宣言を再確認しました。[API source索引](api-audit.md)。
公開Arch ARM zig packageは0.16.0-1だったため、公式0.17.0配布を使う手順を記載しています。

## 実行検証の範囲

この改修で学習対象のZig programは作成していません。Linuxのsyscall、ring、serverの実行は学習者の課題です。
OrbStack CLIはこの作業環境のfilesystem制限で初期化できず、machine内のpackage installと手動実験は実行していません。
OrbStackの操作形式とpackage名は[環境手順](arch-orbstack.md)の一次資料で照合しています。

各章READMEのコマンドは、自作実装後にLinux shell内で実行してください。
