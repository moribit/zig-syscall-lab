# 自己確認 15

`zig build test`はstarterをcompileし、未実装ならSKIPします。trueに変更した後は
`MissingContractTests`が失敗します。READMEの完了条件を満たすassertionをここへ追加し、最後のerrorを置き換えてください。
成功印を付けるだけのtestにはしません。

挙動検査: 同一入力・同一結果と、モデル差を残したinterface設計レポートを提出する。

共通CLI契約とコマンドは[tools](../../tools/README.md)を参照。未実装binaryは非zero終了するため
挙動検査に合格しません。read/writeのpartial転送はネットワーク負荷で必ず発生するとは限らないため、
短い結果やEAGAINを返す偽I/Oをunit testへ注入して検証してください。

試験記録に入力・期待結果・実際・timeout・resource解放を記入します。

## 最低限の試験設計

| 入力/状況 | 期待 | 方法 |
|---|---|---|
| 2 backend同一入力 | byte結果とprotocolが一致 | check.py |
| capability差 | readyとcompletionのownership契約が明示 | 設計レビュー |

偽I/O/偽CQEは学習者が書くtest doubleです。実kernelが必ず短い転送を返すとは仮定しません。
