# 自己確認 09

`zig build test`はstarterをcompileし、未実装ならSKIPします。trueに変更した後は
`MissingContractTests`が失敗します。READMEの完了条件を満たすassertionをここへ追加し、最後のerrorを置き換えてください。
成功印を付けるだけのtestにはしません。

挙動検査: NOPのuser_dataとres=0を確認し、満杯・wraparound・cleanupの試験を追加する。

共通CLI契約とコマンドは[tools](../../tools/README.md)を参照。未実装binaryは非zero終了するため
挙動検査に合格しません。read/writeのpartial転送はネットワーク負荷で必ず発生するとは限らないため、
短い結果やEAGAINを返す偽I/Oをunit testへ注入して検証してください。

試験記録に入力・期待結果・実際・timeout・resource解放を記入します。

## 最低限の試験設計

| 入力/状況 | 期待 | 方法 |
|---|---|---|
| NOP/token42 | CQE user_data=42、res=0 | Linux実機 |
| capacity4/full | 未消費entryを上書きしない | 紙上ring/unit |
| u32 wrap | occupancyとindexが維持される | 境界値unit |

偽I/O/偽CQEは学習者が書くtest doubleです。実kernelが必ず短い転送を返すとは仮定しません。
