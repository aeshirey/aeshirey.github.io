---
layout: post
title:  "Chrono + Serde in Rust"
date:   2021-08-27 21:07:41 -0700
category: code
tags: [rust]
---

By default, `serde` serializes its values (eg, `Date`, `DateTime`) as strings. To save space, particularly when using `rmp_serde`, [`chrono::serde`](https://docs.rs/chrono/0.4.19/chrono/serde/index.html) lets you apply `with = ...` to serialize as seconds, millisec, or nanosec from the epoch:

## Cargo.toml

```toml
[dependencies]
chrono = { version = "0.4.19", features = ["serde"] }
rmp-serde = "0.15.5"
serde = {version = "1.0.106", features = ["derive"]}
serde_json = "1.0.51"
```

## main.rs

```rust
use chrono::{serde::ts_seconds, DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct Record {
    #[serde(with = "ts_seconds")]
    ts: DateTime<Utc>,
}

fn main() {
    // Input value
    let s = "2021-08-28T02:58:17Z";

    // Serialize
    let d = chrono::DateTime::parse_from_rfc3339(s).unwrap();
    let ts: DateTime<Utc> = d.into();
    let rec = Record { ts };
    let j = serde_json::to_string(&rec).unwrap();

    // Using `ts_seconds`, the datetime is serialized to a number:
    assert_eq!(r#"{"ts":1630119497}"#, j);

    // Without `ts_seconds`, this would be serialized instead as: r#"{"ts":"2021-08-28T02:58:17Z"}"#

    // Deserialize
    let Record { ts } = serde_json::from_str(&j).unwrap();
    let ss = ts.to_rfc3339();
    // Explicit timezone is used instead of `Z` for UTC.
    assert_eq!("2021-08-28T02:58:17+00:00", ss);
}
```
