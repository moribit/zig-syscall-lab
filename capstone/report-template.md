# 設計レポート

## 仕様

protocol / message上限 / queue上限 / slow client方針 / graceful shutdown期限:

## backend選択

採用理由、代替方式との比較、kernel制約:

## syscallとblocking point

予想、strace実測、違いの理由:

## ownership

connection / buffer / in-flight operation / task scope / cleanup順の図:

## 10,000接続

fd上限、1接続当たりmemory、queue最大値、公平性、負荷生成器の限界:

## 検証

仕様→test対応表、失敗注入、fd/RSS推移、残る制約:
