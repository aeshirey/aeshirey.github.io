---
layout: post
title:  "Adding built time into your Rust package"
date:   2021-02-12 23:08:10 -0700
category: code
tags: [rust]
---

Given that I'm making reasonably frequent changes to a Rust library at work, I wanted a way to check the build version without having to keep track of the Cargo.toml crate version and in a way that was reliably accessible to any caller of my library. Conceptually, it would be something like:

```rust
const BUILT_ON : &str = compile_time!(); // value gets baked into the application
fn main() {
    println!("This binary was compiled on {}", BUILT_ON);
}
```

As I discovered, it's actually quite easy to do with [build scripts](https://doc.rust-lang.org/cargo/reference/build-scripts.html).

First, we'll start with the build script itself. This is a Rust package (a binary with a `main` function) that gets compiled and executed before our primary crate/package. We'll use the [`OUT_DIR` environment variable](https://doc.rust-lang.org/cargo/reference/environment-variables.html#environment-variables-cargo-sets-for-build-scripts) to give us the directory in which our build is taking place -- the build script will create a small text file, and the main project will read this at compile time. To get the system time, use [`chrono::Local::now()`](https://docs.rs/chrono/0.4.19/chrono/offset/struct.Local.html#method.now):

```rust
use std::{env, io::Write, fs};

fn main() {
    let outdir = env::var("OUT_DIR").unwrap();
    let outfile = format!("{}/timestamp.txt", outdir);

    let mut fh = fs::File::create(&outfile).unwrap();
    write!(fh, r#""{}""#, chrono::Local::now()).ok();
}
```

This script must use `env::var` and not `env!`. We construct the path into which we'll write the value, arbitrarily choosing `timestamp.txt` as the filename. The main project will [`include!`](https://doc.rust-lang.org/std/macro.include.html) that file, so we enquote the timestamp.

`build.rs` is the default filename for build scripts; if you choose to use something else, you have to specify the `build` value in your Cargo.toml in the `[package]` section. Because the build script depends on an external crate, we also specify the required build dependency:

```toml
[package]
build = "my-build.rs"
# ^ or just use 'build.rs' with or without specifying it here ^

[build-dependencies]
chrono = "0.4.19"
```

After building out project, we'll find `timestamp.txt` created for us:


```bash
adam@wsl:~/rust/build-script$ find . | grep timestamp.txt
./target/debug/build/build-script-fa7510033e271b43/out/timestamp.txt
adam@wsl:~/rust/build-script$ cat ./target/debug/build/build-script-fa7510033e271b43/out/timestamp.txt
"2021-02-12 23:22:20.778846100 -08:00"adam@wsl:~/rust/build-script$
```

(This file lacks a trailing newline.)

Now all that remains is to read this file within the main project. Here, we _can_ use `env!` to get the `OUT_DIR`. Concatening that with the desired filename and including those contents into some place that expects a `&str` will work fine:

```rust
const BUILD_TIME : &str = include!(concat!(env!("OUT_DIR"), "/timestamp.txt"));

fn main() {
    println!("This package was compiled at {}", BUILD_TIME);
}
```

Then run it:

```
adam@wsl:~/rust/build-script$ cargo run
   Compiling build-script v0.1.0 (/home/adam/rust/build-script)
    Finished dev [unoptimized + debuginfo] target(s) in 1.03s
     Running `target/debug/build-script`
This package was compiled at 2021-02-12 23:22:20.778846100 -08:00

adam@wsl:~/rust/build-script$ touch src/main.rs

adam@wsl:~/rust/build-script$ cargo run
   Compiling build-script v0.1.0 (/home/adam/rust/build-script)
    Finished dev [unoptimized + debuginfo] target(s) in 0.44s
     Running `target/debug/build-script`
This package was compiled at 2021-02-12 23:25:38.701110700 -08:00
```