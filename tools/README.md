# 仕様検査と測定

Python 3標準ライブラリのみ。学習者のserverは別terminalで起動します。
black-box toolにはserver/file copierの解答実装を含めません。

## CLI契約

file章（02/10/13）: `lab-NN cat PATH`で内容だけstdoutへ、`lab-NN cp SOURCE DEST`で
create/truncateしcopy。診断はstderr、失敗は非zero。13章のcpは発展課題です。
network章: 127.0.0.1:9000でlisten、echoはbyte単位で同一順序、EOF後pending出力を完了してclose。
03章は1接続ずつ、それ以降は複数connection。chatはnewline区切り、送信者以外へ送信。
最大frame4096 byte、per-client未送信queue64KiB、overflow時に当該slow clientを切断します。

```sh
python3 tools/check.py cat --binary zig-out/bin/lab-02
python3 tools/check.py cp --binary zig-out/bin/lab-02
python3 tools/check.py echo                       # 03など
python3 tools/check.py echo --multi               # 05/07/11/12等
python3 tools/check.py chat                       # 08
python3 tools/bench.py --clients 10 --requests 1000 --bytes 64
```

file検査は空・binary・大きな入力、truncate、missing pathの失敗を確認。
echo検査はchunk分割・binary・half-close・再接続、multiはidle client中の進捗を確認。
chatは3接続と分割frameを確認します。slow client/overflow、EINTR、短いwriteの確実な注入、
fd leak、取消回収は別途学習者が追加する試験です。PASSは章の全完了条件ではありません。
04のbusy scanは最大3接続なので4 active + idleのmulti検査は適用せず、3接続で手動確認します。

## benchmarkの読み方

bench.pyは固定接続のclosed-loop（各clientは1 requestずつ待つ）。p50/p95/p99は
成功したrequestの往復msです。timeout/失敗数も表示し、失敗があれば非zero終了します。
throughputの分母には接続開始とwarmupを含むため、steady-state throughputではありません。
比較時は十分長く測り、この条件をレポートに明記します。Python自身のCPU/GILとhost負荷も測ります。
10,000 connectionの測定器としての保証はありません。まず10/100から増やします。

同じbuild mode・payload・接続数・実機条件を固定し最低5反復。JSONを保存し反復間分散を計算します。
serverのCPU/RSSはpidstat/time、syscallは別runのstrace -c、context switchはperfで測定。
外部toolの未導入や権限不足はN/A。wrkはHTTP用なのでraw TCP echoへ直接使いません。

`chapters.json`は章索引です。buildの章一覧変更時も更新してください。
