# Linux I/Oの境界

```text
userspace: buffer / connection state / fd整数 / syscall引数
                         ↓ syscall boundary
kernelspace: fd table → open file description → file/socket/pipe
                         ↓ 待機・転送・通知
userspace: 返却byte数 / errno / ready event / CQE
```

fd tableはprocessに属し、dup等でopen file descriptionを共有するとoffset/status flagsも共有します。
read/writeはkernelとの境界でcopyや待機を行い得ます。mmapはmappingであり自動的なzero-copy保証ではありません。
non-blocking socketのEAGAINは「後で再試行」の状態です。disk fileのO_NONBLOCKは同じ待機回避を保証しません。
poll/epollはreadinessを返しアプリが転送を行います。io_uringは転送要求をsubmitしてcompletionを回収します。

## 実験環境

基本はLinux x86_64/aarch64。epoll/eventfd/io_uringとstrace実験はLinux限定です。
macOSではstarterのbuildと文章読解、Threadedの実験ができますがLinux syscall章はLinuxで実行します。
Lima/UTMなどのVMはkernelを選びやすく、remote Linuxは実機条件を測れます。
Docker/PodmanはLinux kernelを共有し、seccompによるio_uring_setup/enter制限やfd上限があります。

```sh
uname -a
cat /proc/sys/kernel/io_uring_disabled
ulimit -n
ulimit -l
```

sysctlファイルが存在しないkernelもあります。setupやopcodeの利用可否は実際の返却値とprobeで確認します。
ENOSYSは未実装、EPERMはpolicy等、EOPNOTSUPP/EINVALは機能・引数の双方を調査します。
containerの制限を無条件に解除せず、別の学習用VMを選ぶ方法もあります。
benchmarkにはkernel、CPU、VM/container、fd上限、allocator、build modeを記録します。
