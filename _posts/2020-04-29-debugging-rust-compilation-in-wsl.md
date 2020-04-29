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

This is different than [`linker \`cc\` not found`](https://stackoverflow.com/questions/52445961/how-do-i-fix-the-rust-error-linker-cc-not-found-for-debian-on-windows-10). I didn't know that there's actually a [`python3m` executable](https://stackoverflow.com/questions/16675865/difference-between-python3-and-python3m-executables) to which this error message alludes, but it comes with Python. This error is caused by a missing [`libpython3.5-dev` package](https://packages.debian.org/stretch/libpython3.5-dev) (or whatever python version you're using). Install this and it should work:

```bash
sudo apt install libpython3.5-dev
```
