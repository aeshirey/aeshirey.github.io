---
layout: post
title:  "Benchmarkng MsgPack vs JSON in Rust"
date:   2020-11-25 00:03:10 -0700
category: code
tags: [rust]
---

After implementing [MessagePack in Rust for Python](https://aeshirey.github.io/code/2020/10/21/messagepack-and-pyo3.html) and comparing serialized MessagePack versus JSON for a HyperLogLog data structure, I wanted to check the performance of the two.

Not needing PyO3 for this one, I wrote a straightforward `main.rs` with a few functions for testing ser/de for both formats:


```rust
#![feature(test)]
extern crate test;
// ...

#[bench]
pub fn ser_bytes(b: &mut test::Bencher) {
    let hll = HyperLogLog::<String>::new_from_keys(0.01, 123, 456);

    b.iter(|| {
        rmp_serde::to_vec(&hll).unwrap();
    });
}

#[bench]
pub fn ser_str(b: &mut test::Bencher) {
    let hll = HyperLogLog::<String>::new_from_keys(0.01, 123, 456);

    b.iter(|| {
        let _json = serde_json::to_string(&hll).unwrap();
    });
}

// Corresponding deserializing functions omitted
```

I then tested the four functions with `cargo bench`:
```
running 4 tests
test de_bytes  ... bench:       5,594 ns/iter (+/- 1,906)
test de_str    ... bench:      18,532 ns/iter (+/- 9,107)
test ser_bytes ... bench:      24,962 ns/iter (+/- 15,104)
test ser_str   ... bench:      18,363 ns/iter (+/- 3,592)
```

Based on this, it appears that MessagePack deserializes at 30% the time of JSON but serializes at 135%.
