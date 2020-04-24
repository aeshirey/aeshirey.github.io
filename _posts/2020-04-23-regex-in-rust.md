---
layout: post
title:  "Regex in Rust"
date:   2020-04-23 18:57:25 -0700
category: code
tags: [rust]
---

In working on my `.eml` parser library, [`EmlParser`](https://github.com/aeshirey/EmlParser/), I decided using a regex would be way easier than trying to roll my own parser for handling RFC-0822's definition for `route-addr`. But I hadn't yet used regular expressions in Rust, so voilà:

#### Cargo.toml

```ini
[dependencies]
regex = "1"
```

#### main.rs

```rust
use regex::Regex;

fn main() {
    let email = r#""John Smith" <jsmith@example.com>"#;

    let name_addr_re = Regex::new(r#""(.?+)" <([^>]+)>"#).unwrap();
    let addr_re = Regex::new(r#""(.?+)" <([^>]+)>"#).unwrap();

    match name_addr_re.captures(email) {
        Some(cap) => {
            let name = cap.get(1).unwrap();
            let addr = cap.get(2).unwrap();

            let namestr : &str = name.as_str();

            println!("I found name = {}", name.as_str()); // "John Smith"
            println!("I found addr = {}", addr.as_str()); // "jsmith@example.com"
        },
        None => println!("doh!?")
    };
}
```

The hardest part seems to be figuring out the Rust API ([`regex` docs here](https://docs.rs/regex/1.3.7/regex/struct.Regex.html)) -- `.captures` gets you what's analogous to Python's [`Match.group`](https://docs.python.org/3/library/re.html#re.Match.group), etc.
