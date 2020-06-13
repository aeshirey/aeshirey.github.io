---
layout: post
title:  "Simple C library with Rust"
date:   2020-06-13 07:14:49 -0700
category: code
tags: [rust]
---

Create a simple C library, `c-code/my-library.c`:

```c
int square(int num) {
    return num * num;
}
```

This step is _not_ needed for this post, but we could compile this with `cc -c my-library.c` to build `my-library.o`:

```bash
$ cc my-library.c -c
$ ls
my-library.c  my-library.o
$ file my-library.o
my-library.o: ELF 64-bit LSB relocatable, x86-64, version 1 (SYSV), not stripped
```

Hook it into some Rust code:

```rust
#[link(name="mylib")]
extern "C" {
    fn square(val: i32) -> i32;
}

fn main() {
    let sq = unsafe { square(3) };
    println!("3**2 = {}", sq);
}
```

This tells Rust that we have a library `mylib` containing a `square` function. It's considered [`unsafe`](https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html) and must be wrapped as such. But in order to let Rust access this library, we need a `build.rs` [build script](https://doc.rust-lang.org/cargo/reference/build-scripts.html) located at the _root_ of our crate (not in the `src/` folder):

```rust
fn main() {
    // Recompile if my-library.c is updated
    println!("cargo:rerun-if-changed=src/my-library.c");

    // Use the `cc` crate to build a C file and statically link it.
    cc::Build::new()
        .file("c-code/my-library.c")
        .compile("mylib");
```

Note that this build script bridges the name of our file (`my-library.c`) and the library name (`mylib`). Since this is using the [`cc` crate](https://crates.io/crates/cc), we have to included it in the `Cargo.toml`:

```toml
[build-dependencies]
cc = "1.0.46"
```

With this, we're set:

```bash
$ cargo run
   Compiling simple-ffi v0.1.0 (/mnt/c/Users/adam/c)
    Finished dev [unoptimized + debuginfo] target(s) in 0.80s
     Running `target/debug/c`
3**2 = 9
```
