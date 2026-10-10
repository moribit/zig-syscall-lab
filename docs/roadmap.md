# 学習ロードマップ

```text
fd → raw file I/O → blocking TCP → non-blocking TCP
→ poll → epoll fundamentals → echo → chat
→ 12: 自作event loop → 09: io_uring ring → file → network
→ std.Io → async/concurrency → モデル比較 → benchmark → capstone
```

01–02: fdとbyte数。03–05: 待機と空振り。06–08: readinessとconnection state。
12: 状態機械・wake・公平性。09–11: completionとin-flight ownership。
13–14: 依存注入とtask scope。15–16: 抽象化の限界と測定。

各段階の成果物は自作source、仕様test、trace、予想と差のnotesです。
前章のbuffer lifetimeやpartial I/Oが曖昧なら、先へ進む前に1 byte実験へ戻ります。
12という番号が09より後に見えても、08の「次章への問い」から12へ進んでください。
