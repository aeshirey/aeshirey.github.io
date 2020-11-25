---
layout: post
title:  "Debugging Rust compilation (in WSL)"
date:   2020-04-29 11:18:46 -0700
category: code
tags: [rust]
---

#### Linking with `cc` failed
Some errors I've encountered trying to compile (typically just `cargo build`):

```
...
error: linking with `cc` failed: exit code: 1
  |
  = note: "cc" "-Wl,--as-needed...
  (several screens of linker arguments omitted)
  = note: /usr/bin/ld: cannot find -lpython3.5m
          collect2: error: ld returned 1 exit status


error: aborting due to previous error; 10 warnings emitted
```

This is different than [`linker 'cc' not found`](https://stackoverflow.com/questions/52445961/how-do-i-fix-the-rust-error-linker-cc-not-found-for-debian-on-windows-10), which is a common problem just after installing Rust in WSL and should be fixed by simply running `apt get install build-essential`. I didn't know that there's actually a [`python3m` executable](https://stackoverflow.com/questions/16675865/difference-between-python3-and-python3m-executables) to which this error message alludes, but it comes with Python. This error is caused by a missing [`libpython3.5-dev` package](https://packages.debian.org/stretch/libpython3.5-dev) (or whatever python version you're using). Install this and it should work:

```bash
sudo apt install libpython3.5-dev
```

## Publishing crates
`cargo publish` has an issue in [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install-win10) that yields a rather useless error:

    adam@wsl:/mnt/c/Users/adam/source/repos/probably$ cargo publish
    ...
    Uploading probably v0.2.0 (/mnt/c/Users/adam/source/repos/probably)
    error: No such file or directory (os error 2)

This is caused by WSL2's inability to access Windows mounts (since WSL2 runs in a VM unlike WSL). It [can be fixed](https://github.com/rust-lang/cargo/issues/8439#issuecomment-660310563) by simply copying your folder over to, say, `~`, then doing a publish from that directory:

    adam@wsl:/mnt/c/Users/adam/source/repos$ cp -r probably ~
    adam@wsl:/mnt/c/Users/adam/source/repos$ cd ~/probably
    adam@wsl:~/probably$ cargo publish
    ...
    Uploading probably v0.2.0 (/home/adam/probably)
    adam@wsl:~/probably$ 
