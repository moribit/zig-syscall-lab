# 標準環境: M2 MacBook Air + OrbStack + Arch Linux ARM64

教材はLinux x86_64/aarch64を対象にします。標準の学習環境はM2のARM64 Linux machineです。
OrbStackの[Arch対応](https://docs.orbstack.dev/machines/distros)、[machine作成](https://docs.orbstack.dev/machines/)、
[shell操作](https://docs.orbstack.dev/machines/commands)を確認してからmacOSで実行します。

```sh
orb create arch zig-syscall-lab
orb -m zig-syscall-lab
```

Linux shellに入ったら`uname -a`と`uname -m`を記録します。期待architectureはaarch64です。
同名machineが既にある場合は再作成せず、そのmachineへ入ります。

## Linux package

Archはrolling releaseなので、full system upgrade後に導入します。

```sh
sudo pacman -Syu
pacman -Si strace man-db man-pages neovim socat openbsd-netcat git
sudo pacman -S strace man-db man-pages neovim socat openbsd-netcat git
```

2026-10-10に以下の一次資料でpackage名を確認しました。ARMのman-pagesページは取得できず、
Arch本体のarchitecture=anyのpackageで名称を確認しています。最終的なmachine内の提供状況は上のpacman -Siで確認します。

| 用途 | package名・一次資料 |
|---|---|
| syscall観測 | [strace](https://archlinuxarm.org/packages/aarch64/strace) |
| man reader | [man-db](https://archlinuxarm.org/packages/aarch64/man-db) |
| Linux API manual | [man-pages (any)](https://archlinux.org/packages/core/any/man-pages/) |
| editor (nvim) | [neovim](https://archlinuxarm.org/packages/aarch64/neovim) |
| socket実験 | [socat](https://archlinuxarm.org/packages/aarch64/socat)、[openbsd-netcat (nc)](https://archlinuxarm.org/packages/aarch64/openbsd-netcat) |
| 学習履歴 | [git](https://archlinuxarm.org/packages/aarch64/git) |
| 任意debugger | [gdb](https://archlinuxarm.org/packages/aarch64/gdb) |
| 任意性能counter | [perf](https://archlinuxarm.org/packages/aarch64/perf) |
| pidstat / resource時間 | [sysstat](https://archlinuxarm.org/packages/aarch64/sysstat)、[time](https://archlinuxarm.org/packages/aarch64/time) |
| download / source検索 | [curl](https://archlinuxarm.org/packages/aarch64/curl)、[ripgrep (rg)](https://archlinuxarm.org/packages/aarch64/ripgrep) |

必要な時だけ追加します。

```sh
sudo pacman -S gdb perf sysstat time curl ripgrep
man 2 write
```

## Zig 0.17.0を固定する

[Arch Linux ARMのzig package](https://archlinuxarm.org/packages/aarch64/zig)は確認時0.16.0-1でした。
package名zigは存在しますが、この教材versionを満たすとは限りません。
`pacman -Si zig`と`zig version`を確認し、違う場合は[公式配布](https://ziglang.org/download/)の
0.17.0 aarch64-linux版を使います。Linux shellで、例として次の場所へ展開します。

```sh
mkdir -p "$HOME/.local/opt"
cd "$HOME/.local/opt"
curl -fLO https://ziglang.org/download/0.17.0/zig-aarch64-linux-0.17.0.tar.xz
tar -xf zig-aarch64-linux-0.17.0.tar.xz
export PATH="$HOME/.local/opt/zig-aarch64-linux-0.17.0:$PATH"
zig version
zig env
```

versionの出力は0.17.0である必要があります。PATHは使うLinux shellの設定にも追記し、
次のterminalでもversionを再確認します。x86_64 Linuxなら公式x86_64-linux版を選びます。
macOS版のzigやbinaryをこのLinux実験に使わないでください。

## 同じ環境で編集・実行する

```sh
git clone https://github.com/moribit/zig-syscall-lab.git
cd zig-syscall-lab/01-file-descriptor
export EDITOR=nvim
touch main.zig
$EDITOR main.zig
zig run main.zig
```

空fileはまだ実行できません。READMEを読み、importとmainから自分で書いてください。
editor、コンパイル、実行、straceをLinux内に揃えると、fdやpathとOSの境界を取り違えにくくなります。
二つ目のterminalも`orb -m zig-syscall-lab`で同じmachineへ入ります。

macOS側で編集する補足: OrbStackは[共有file](https://docs.orbstack.dev/machines/file-sharing)に対応します。
Linux内のrepoをMac editorから開く場合も、実行するzigのtargetとworking directoryはLinuxで確認します。
共有filesystemとLinux内filesystemはbenchmark条件として区別してください。

## kernelと実験の制約

io_uringはkernel/feature/policy/resource制限に依存します。setupのerrnoとopcodeの可否を実測し、
使えなければ利用可能な別Linux machineへ移る方法もあります。perfもVM内でhardware counterが利用できない場合があります。
詳しくは[Linux I/Oの境界](linux-io-overview.md)。この環境手順の掲載はmachine作成やpackage導入の実行検証を意味しません。
