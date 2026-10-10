# 自己確認 16

`zig build test`はstarterをcompileし、未実装ならSKIPします。trueに変更した後は
`MissingContractTests`が失敗します。READMEの完了条件を満たすassertionをここへ追加し、最後のerrorを置き換えてください。
成功印を付けるだけのtestにはしません。

挙動検査: testを先に通し、CSV/JSONと測定条件・反復間分散・p99・失敗数をレポートする。

共通CLI契約とコマンドは[tools](../../tools/README.md)を参照。未実装binaryは非zero終了するため
挙動検査に合格しません。read/writeのpartial転送はネットワーク負荷で必ず発生するとは限らないため、
短い結果やEAGAINを返す偽I/Oをunit testへ注入して検証してください。

試験記録に入力・期待結果・実際・timeout・resource解放を記入します。

## 最低限の試験設計

| 入力/状況 | 期待 | 方法 |
|---|---|---|
| timeout/failure | 失敗数を含み非zero終了 | bench.py |
| 5反復 | 条件固定で分散とpercentileを記録 | JSON比較 |
| 負荷生成器CPU | serverとのbottleneck区別 | pidstat |

偽I/O/偽CQEは学習者が書くtest doubleです。実kernelが必ず短い転送を返すとは仮定しません。
