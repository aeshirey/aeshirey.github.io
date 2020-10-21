---
layout: post
title:  "MessagePack and PyO3"
date:   2020-10-20 20:52:57 -0700
category: code
tags: [rust, python, pyo3]
---

I really like [`serde`](https://serde.rs/) and have been using it a good deal for JSON serialization/deserialization, but one of my projects is using a [HyperLogLog data structure with serialization](https://github.com/aeshirey/rust-hyperloglog/), which ends up using quite a lot of space. I did some poking around and found that it supports [MessagePack](https://msgpack.org/) -- a format I've never used but that appears promising for reducing the size of serialized data. So I ran a test that serializes a HLL data structure to MessagePack and to JSON to compare the sizes. Also, since I'm accessing the data from Python, I also dived into how to use PyO3's [`PyBytes`](https://github.com/PyO3/pyo3/blob/151af7a0b702febed4cd34669a0401942a413f83/src/types/bytes.rs#L18) that will return a Python `bytes` object.


## Specify dependencies
We need PyO3, serde (both JSON and MessagePack), and my HLL fork:

```toml
[dependencies.pyo3]
version = "0.12.3"
features = ["extension-module"]

[dependencies]
serde = {version = "1.0.106", features = ["derive"]}
serde_json = "1.0.51"
rmp-serde = "0.14.4"

hyperloglog = { git = "https://github.com/aeshirey/rust-hyperloglog", features = ["with_serde"] }
```

## Some pyfunctions
Write some functions that will create an empty `HyperLogLog<String>` with a 1% error rate and hard-coded hash keys. One function serializes to `bytes` and one to a JSON `str`.

```rust
#[pyfunction]
pub fn hll_bytes(py: Python) -> &PyBytes {
    let hll = HyperLogLog::<String>::new_from_keys(0.01, 123, 456);

    let mut buf: Vec<u8> = Vec::new();
    let mut rmp_ser = rmp_serde::Serializer::new(&mut buf);
    hll.serialize(&mut rmp_ser).unwrap();

    let b = PyBytes::new(py, &buf[..]);
    b
}

#[pyfunction]
pub fn hll_str(_py: Python) -> String {
    let hll = HyperLogLog::<String>::new_from_keys(0.01, 123, 456);

    let s = serde_json::to_string(&hll).unwrap();
    s
}
```

## Deserializing
For reference, here's how we'd deserialize the objects when passed from Python to Rust:
```rust
pub fn hll_from_bytes<'a>(py: Python<'a>, b: &'a PyBytes) {
    let mut rmp_deser = rmp_serde::Deserializer::new(&b[..]);
    let mut hll: HyperLogLog<String> = serde::Deserialize::deserialize(&mut rmp_deser).unwrap();

    // Alternately:
    // let hll: HyperLogLog<String> = rmp_serde::from_slice(&b[..]).unwrap();

    // ...
}

pub fn hll_from_string(_py: Python, s: String) {
    let mut hll : HyperLogLog<String> = serde_json::from_str(&s).unwrap();

    // ...
}
```

## Accessing from Python
Now that there are functions that will return a serialized HLL, we can access them from Python:
```python
import hll_serde # my PyO3 library
b = hll_serde.hll_bytes() # len=1045
s = hll_serde.hll_str()   # len=2120

# MessagePack is about 49% the size of the JSON
# Let's try compressing them both with gzip:
import gzip
b_gz = gzip.compress(b) # len=49
s_gz = gzip.compress(s.encode('utf-8')) # len=102
```

Gzipped, they're both significantly smaller, but MessagePack is again about the same ratio -- gzipped MessagePack is 48% as big as gzipped JSON.

But these are _empty_ HyperLogLog data structures. So if we insert a bunch of data into them, we can see how that will affect their serialization.

```python
import glob
files = glob.glob('/tmp/*') # len=127
for file in files:
    # Implementation of the insert_bytes and insert_str not shown. They just
    # accept their respective serialized HLL, insert the passed string, and
    # return the serialization of the updated HLL (not in-place)
    b = hll_serde.insert_bytes(b, file)
    s = hll_serde.insert_str(s, file)

hll_serde.hll_count_bytes(b) # 126.5017465851157
hll_serde.hll_count_str(s)   # 126.5017465851157
```

At this point, we've inserted 127 values into each HLL. It's important to note that because they're generated with the same acceptable error rate and the same hash keys, these are identical data structures -- we're just serializing them differently to send them back to Python. And the size of the data structures aren't changing -- the `len` of the empty and modified `bytes` HLLs are the same. But now that the content has changed, we can check how this affects compression:

```python
len(gzip.compress(b)) # 220
len(gzip.compress(s.encode('utf-8'))) # 279
```

Again, gzipping significantly reduces the size. Now that there's variation in the data, we don't see as stark a contrast: MP is now 79% the size of JSON.

## Performance
This post doesn't address the performance implications of ser/de of a large/complex data structure into the two formats nor the gzipping from Python if you want to further reduce size. That's covered in my next post.
