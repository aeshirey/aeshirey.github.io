---
layout: post
title:  "GZip encoding and decoding in Python"
date:   2020-07-19 15:33:06 -0700
category: code
tags: [python, rust]
---

After [testing GZip encoding/decoding in Rust](https://aeshirey.github.io/code/2020/07/05/gzip-encoding-and-decoding-in-rust.html), I wanted to benchmark against comparable Python. The Python code is unsurprisingly concise:

```python
import gzip

in_fn = "input.gz"
out_fn = "output.gz"

with gzip.open(in_fn, 'rt') as in_gz:
    with gzip.open(out_fn, 'wt') as out_gz:
        for line in in_gz:
            out_gz.write(line)
```

To test the _performance_ difference, I first wrote some Rust code to generate a bunch of random data (because I wanted more practice with Rust). So I created a new project that uses `rand = "0.7"`. The code is:

```rust
use rand;

// Characters generated will be between the lower and upper limits, inclusive.
const LOWER_LIMIT: u8 = 32;
const UPPER_LIMIT: u8 = 126;

// Size of the buffer
const BUF_SIZE : usize = 100_000;

fn main() {
    let mut bytes_to_generate = 1_000_000_000;


    let mut buf = String::with_capacity(BUF_SIZE);
    while bytes_to_generate > 0 {
        for _ in 0..BUF_SIZE {
            let n: u8 = rand::random::<u8>() % (UPPER_LIMIT - LOWER_LIMIT + 1) + LOWER_LIMIT;
            buf.push(n as char)
        }

        println!("{}", buf);
        buf.clear();
        bytes_to_generate -= BUF_SIZE;
    }
}
```

A gigabyte of uniformly-distributed ASCII data isn't exactly realistic but probably sufficient. After building release, I ran this and redirected it into a text file:

```bash
time ./target/release/generate-random-data > random_data.txt

real    0m7.324s
user    0m5.422s
sys     0m0.516s

$ ls -lh random_data.txt
-rw-r--r-- 1 adam adam 954M Jul 19 15:17 random_data.txt
```

Using the i/o buffering makes this super fast, and increasing the buffer size from 100 to 100k bytes by orders of magnitude drops the time from over a minute to around seven seconds:

| Buffer Size | Time (sec) |
|------------:|-----------:|
| 100         | 64.978     |
| 1000        | 12.612     |
| 10000       | 7.989      |
| 100000      | 6.591      |

Next I gzipped this input, dropping the file size from 954M to 790M in 37.1 seconds. I then ran the Python code and timed how long it takes to gunzip and gzip the stream:

```bash
$ time python3 test-gzip.py

real    0m49.169s
user    0m42.859s
sys     0m4.313s
```

Running my comparable Rust code against the same input:

```bash
$ time ./target/release/gzip-rs

real    0m27.968s
user    0m25.969s
sys     0m1.047s
```

Since my original code was using a buffer size of 10kb and since the above example shows how much buffer size can affect i/o, I increased the size for this example to 100\_000 and re-ran:

```bash
$ time ./target/release/gzip-rs

real    0m27.735s
user    0m25.453s
sys     0m1.094s
```

Apparently I have hit diminishing returns with my buffer capacity. However, the Rust code is significantly faster than Python. The latter takes 77% longer than the former. If there exists a way to specify buffering within the Python code, that may speed it up, but I'm not aware of such a way.
