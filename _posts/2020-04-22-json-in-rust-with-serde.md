---
layout: post
title:  "JSON in Rust with serde"
date:   2020-04-22 19:30:02 -0700
category: code
tags: [rust]
---

Simple object *ser*ialization and *de*serialization in Rust with [`serde`](https://serde.rs/).

#### Cargo.toml

```ini
[dependencies]
serde = {version = "1.0.106", features = ["derive"]}
serde_json = "1.0.51"
```

#### main.rs

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct Person {
    name: String,
    age: u8,
    gender: Option<char>,
    aliases: Vec<String>,
    deceased: bool,
}

fn main() {
    let bilbo = Person {
        name: "Bilbo Baggins".to_string(),
        age: 111,
        gender: Some('m'),
        aliases: vec!["Thief".to_string()],
        deceased: false,
    };

    let bilbo_json =
        r#"{"name":"Bilbo Baggins","age":111,"gender":"m","aliases":["Thief"],"deceased":false}"#;

    let serialized = serde_json::to_string(&bilbo).unwrap();

    assert_eq!(bilbo_json, serialized);
}
```

What's even cooler is that [`enum` deserialization](https://serde.rs/enum-representations.html) can be [untagged](https://serde.rs/enum-representations.html#untagged), meaning 

> Serde will try to match the data against each variant in order and the first one that deserializes successfully is the one returned.
