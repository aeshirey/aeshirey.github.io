---
layout: post
title:  "GZip encoding and decoding in Rust"
date:   2020-07-05 16:54:01 -0700
category: code
tags: [rust]
---

I discovered the [`flate2` crate](https://github.com/alexcrichton/flate2-rs) the other day, so I decided to take it for a spin. First, add the dependency:

```toml
[dependencies]
flate2 = "1.0"
```

Then I wrote a simple binary that will gzip-decode a text file, `input.gz`, and gzip-encode the same data (for simplicity) to `output.gz`:

```rust
use flate2::read::GzDecoder;
use flate2::write::GzEncoder;
use flate2::Compression;
use std::io;
use std::io::prelude::*;

// Using a different capacity than the default 8k - no particular reason,
// though there may be optimizations here knowing we're dealing with zipped data?
const CAPACITY: usize = 10240;

fn main() {
    // Input values:
    let in_filename = "input.gz";
    let in_fh = std::fs::File::open(in_filename).unwrap();
    let in_gz = GzDecoder::new(in_fh);
    let in_buf = io::BufReader::with_capacity(CAPACITY, in_gz);

    // Output values:
    let out_filename = "output.gz";
    let out_fh = std::fs::File::create(out_filename).unwrap();
    let out_gz = GzEncoder::new(out_fh, Compression::default());
    let mut out_buf = io::BufWriter::new(out_gz);

    // BufRead strips \n and \r from the end, so we'll tack on a newline.
    // The input and output may therefore differ in their line endings.
    for line in in_buf.lines() {
        let line = line.unwrap();
        let line_bytes = line.as_bytes();

        out_buf.write(&line_bytes);
        out_buf.write(b"\n");
    }

    out_buf.flush();
}
```
