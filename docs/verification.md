# 教材構造の検証記録

2026-10-10 / Zig 0.17.0 / aarch64-macos。
この記録は未実装starterと教材の検証で、学習者の完成実装の動作保証ではありません。

| 検査 | 結果 |
|---|---|
| root zig build | 成功、17 starterをcompile/install |
| root zig build test --summary all | 成功、17件SKIP、pass 0件 |
| zig build chapter -Dchapter=06 | 成功、選択chapterをinstall |
| 全16章 + capstoneの単独zig build test | 全て成功、各1件SKIP |
| root -Dtarget=x86_64-linux | cross build成功 |
| root -Dtarget=aarch64-linux | cross build成功 |
| tools/api-check.zigのnative test | 1件pass |
| 同probe Linux x86_64/aarch64 -fno-emit-bin | compile成功（Linux実行なし） |
| Python toolsのpy_compile | 成功 |
| check.pyで未実装catを検査 | 意図したFAIL/nonzero |
| bench.pyで接続不可portを検査 | success=0/errors=1/nonzero、percentile=null |
| required見出し、starter未実装、local文書link | 全17章で確認 |

cache書込みを許可領域に収めるため、検証時は`ZIG_GLOBAL_CACHE_DIR=/tmp/zig-io-lab-global`と
`--cache-dir /tmp/zig-io-lab-cache`等を指定しました。cross build出力も/tmpへ配置しました。
通常の学習コマンドはroot READMEに記載しています。

## 今後Linux上で行う検証

- 学習者実装のsyscall trace、fd/RSS leak、signal/EINTR、partial I/O
- LT/ET実験、eventfd wake race、stale token
- io_uringのmapping、NOP、CQEと各opcodeのfeature確認
- normal echo/chatに対する外部検査の実機実行
- std.Io backendとcancel pointの動作、task scope終了時cleanup
- 公平なbenchmark（失敗数・負荷生成器bottleneck・環境条件込み）

完成server/file copierは意図的に未実装です。test TODOやSKIPは教材の余白であり解答を追加しません。
より発展的なmultishot、registered buffer、zero-copyは発展課題です。
