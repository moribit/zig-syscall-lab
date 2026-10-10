# 用語集

| 用語 | この教材での意味 |
|---|---|
| syscall | userspaceからkernelへ処理を依頼する入口 |
| userspace | アプリが動く保護されたアドレス空間 |
| kernelspace | kernelの権限と管理領域。アプリは直接自由に触れない |
| fd | processのdescriptor tableの整数索引。close後に再利用される |
| blocking | 条件成立まで呼出threadが待つ可能性がある |
| non-blocking | 今進めない場合にEAGAIN等で戻り、後で再試行する |
| synchronous | 呼出の返却時にその操作の結果を受け取るモデル |
| asynchronous | 開始と結果取得が分離されるモデル。別threadとは限らない |
| concurrency | 複数の仕事が同じ期間に進行し得ること |
| parallelism | 複数の仕事が同時刻に実行されること |
| readiness | 今I/Oを試せるという通知。成功や全転送の保証ではない |
| completion | 依頼したoperationの結果。成功・短い転送・失敗を含む |
| reactor | ready通知を受けたアプリがI/Oとdispatchを行う構造 |
| proactor | I/Oを先に依頼し、完了結果をdispatchする構造 |
| event loop | 待機とevent dispatchを繰り返して仕事を進める仕組み |
| polling | 状態を調べる行為。poll syscallとbusy pollingを区別する |
| busy loop | 有用な進捗がない時も待機せず反復してCPUを使うloop |
| backpressure | 生産速度を消費速度・queue容量に合わせて抑えること |
| buffer | byteを一時保持する領域。長さ・容量・所有者・寿命が必要 |
| zero-copy | 特定区間のcopyを省く技術。全経路でcopyがないとは限らない |
| mmap | file/device等を仮想address spaceへmapする操作 |
| ring buffer | head/tailとwraparoundで循環利用する有限queue |
| SQ | Submission Queue。kernelへ渡す要求のqueue |
| CQ | Completion Queue。kernelから返る結果のqueue |
| SQE | Submission Queue Entry。opcode、fd、buffer等の要求 |
| CQE | Completion Queue Entry。user_data、res、flags等の結果 |
| EINTR | signalでsyscallが中断された状態。wrapperによるretryに注意 |
| EOF | stream終端。非空read要求の0返却で判定する |
| LT | level-triggered。ready条件が残る間再通知され得る |
| ET | edge-triggered。変化を通知する。EAGAINまでdrainする設計が必要 |
| ownership | resourceを解放する責任と参照の有効期間 |
| structured concurrency | 子taskの寿命をscopeへ結び、退出前に完了/取消を回収する設計 |
