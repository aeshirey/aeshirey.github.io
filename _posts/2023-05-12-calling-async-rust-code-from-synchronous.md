---
layout: post
title:  "Calling async Rust code from synchronous"
date:   2023-05-12 19:42:52 -0700
category: code
tags: [rust]
---

Sometimes I find that I have some `async` code that I really want to call from another project, but I don't want `async`/`await` to infect my entire codebase. At least using [`tokio`](https://docs.rs/tokio/latest/tokio/), there's an easy way to do this. Given some async project:

```bash
cargo new --lib my-async-crate
cargo add tokio
```

Which exposes an `async` function:

```rust
pub async fn sleep_a_bit(num_seconds: u64) {
    println!("Hold please...");
    tokio::time::sleep(std::time::Duration::from_secs(num_seconds)).await;
    println!("Thanks for waiting!");
}
```

We then have a project which wants to use our cool `sleep_a_bit` function:

```bash
cargo new my-project
```

```rust
fn main() {
    my_async_crate::sleep_a_bit(5);
}
```

This compiles, but it doesn't do what we want:

```ignore
warning: unused implementer of `Future` that must be used
 --> src/main.rs:2:5
  |
2 |     my_async_crate::do_async_await(5);
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |
  = note: futures do nothing unless you `.await` or poll them
  = note: `#[warn(unused_must_use)]` on by default
```

If we run this project, it will immediately exit. Thus, we need to include the `.await` call:

```rust
fn main() {
// ---- this is not `async`
    my_async_crate::sleep_a_bit(5).await;
    //                             ^^^^^^ only allowed inside `async` functions and blocks
}
```

What we need is to create a tokio [`Runtime`](https://docs.rs/tokio/latest/tokio/runtime/struct.Runtime.html) that can synchronously block until the inner asynchronous operations complete. To do this, we add tokio with the `rt` feature:

```bash
cargo add tokio --features rt
```

The main function then creates the runtime and creates a `Future`. For this example, we'll just [`block_on`](https://docs.rs/tokio/latest/tokio/runtime/struct.Runtime.html#method.block_on):

```rust
fn main() {
    let rt = tokio::runtime::Runtime::new().unwrap();

    rt.block_on(async {
        my_async_crate::sleep_a_bit(5).await;
        println!("And we're back!");
    });
}
```

