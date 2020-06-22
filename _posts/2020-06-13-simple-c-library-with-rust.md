---
layout: post
title:  "Simple C library with Rust"
date:   2020-06-13 07:14:49 -0700
category: code
tags: [rust]
---

## Statically-linked
Create a simple C library, `c-code/my-library.c`:

```c
int square(int num) {
    return num * num;
}
```

This step is _not_ needed for static linking (because we'll use the Rust toolchain to do it for us), but we _could_ compile this to an object file:

```bash
$ cc my-library.c -c
$ ls
my-library.c  my-library.o
$ file my-library.o
my-library.o: ELF 64-bit LSB relocatable, x86-64, version 1 (SYSV), not stripped
```

Write some Rust code that will make use of it. We have to tell Rust that there exists an external function named `square` that takes and returns an unsigned 32-bit int:

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

Our function is considered [`unsafe`](https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html) and must be wrapped as such. But in order to let Rust access this library, we need a `build.rs` [build script](https://doc.rust-lang.org/cargo/reference/build-scripts.html) located at the _root_ of our crate (not in the `src/` folder):

```rust
fn main() {
    // Recompile if my-library.c is updated
    println!("cargo:rerun-if-changed=c-code/my-library.c");

    // Use the `cc` crate to build a C file and statically link it.
    cc::Build::new()
        .file("c-code/my-library.c")
        .compile("mylib");
}
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

# Dynamically-linked
We can also dynamically link to a shared object (`.so`) file instead. The `Cargo.toml` file no longer needs the `[build-dependencies]` section.

The Rust binary no longer needs to specify that it's linking to a library:

```rust
//#[link(name="mylib")] <-- this line not needed
extern "C" {
    fn square(val: i32) -> i32;
}

fn main() {
    let sq = unsafe { square(3) };
    println!("3**2 = {}", sq);
}
```

To compile our program, `rustc` will need to know about the library. Therefore, our `build.rs` script specifies [`rustc-link-search`](https://doc.rust-lang.org/cargo/reference/build-scripts.html#rustc-link-search) in order to know _where_ the library is during compilation. The build script also specifies that we want to _dynamically_ link to the dylib `my-library`.

```rust
fn main() {
    println!("cargo:rustc-link-search=native=c-code/"); // +
    println!("cargo:rustc-link-lib=dylib=my-library");
}
```
**NOTE** that while we're calling the library `my-library`, the linker actually looks for a file with a 'lib' prefix, `libmy-library.so`, so we have to compile it accordingly:

```bash
$ gcc c-code/my-library.c -shared -o libmy-library.so

$ ls *.so
libmy-library.so

$ file libmy-library.so
libmy-library.so: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, BuildID[sha1]=49953c0cb91c9212594e24e6e3c3ee531f06a9df, not stripped
```

We should be able to build now:

```bash
$ cargo build
   Compiling simple-ffi v0.1.0 (/mnt/c/Users/adam/c)
    Finished dev [unoptimized + debuginfo] target(s) in 0.67s

$ ./target/debug/simple-ffi
./target/debug/simple-ffi: error while loading shared libraries: libmy-library.so: cannot open shared object file: No such file or directory

$ ldd target/debug/simple-ffi
        linux-vdso.so.1 (0x00007fffe5d32000)
        libmy-library.so => not found
        libdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007f7c61a70000)
        librt.so.1 => /lib/x86_64-linux-gnu/librt.so.1 (0x00007f7c61860000)
        libpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007f7c61640000)
        libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1 (0x00007f7c61420000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f7c61020000)
        /lib64/ld-linux-x86-64.so.2 (0x00007f7c62000000)
```

The binary file can't find the library at runtime, and running `ldd` shows that it's attempting and failing to dynamically load the shared object file we compiled. Even if that file is in the same directory, it doesn't work because that's not how Linux loads its shared objects. You have to either copy the .so file into a folder specified by `LD_LIBRARY_PATH` or update your `LD_LIBRARY_PATH` when running. The quick fix is to do the latter:

```bash
$ LD_LIBRARY_PATH=. ./target/debug/simple-ffi
3**2 = 9
```

## Additional details

If you compile with the `-c` flag instead of `-shared`, even with the `build.rs` script and `main.rs` setup for dynamic linking, it appears that the library will be statically linked. I haven't dived into this much, but in writing this post, I ran into my hopefully-dynamically linked accidentally being statically linked.
