---
layout: post
title:  "Name parsing in Rust"
date:   2020-04-11 20:17:07 -0700
category: code
tags: [rust]
---

Some years ago, I wrote [`NameParserSharp`, a C# name parsing library](https://github.com/aeshirey/NameParserSharp/) for a personal need. I [published it on NuGet](https://www.nuget.org/packages/NameParserSharp/), and I was recently surprised to find it had over 83k downloads -- not a huge number compared to other libraries, but way more than I had expected. So as I've been trying to find something to do with my exploits in Rust, I decided this would be a reasonable baby step toward producing something more than toy `Hello, World!` projects.

I have spent the last few days poking around with trying to implement something analogous in Rust. Today, I have now published [`NameParser` v0.1.0 on crates.io](https://crates.io/crates/NameParser). Usage looks like this:

```rust
let p = PersonName::parse("Johannes Diderik van der Waals").unwrap();
assert_eq!(p.first, "Johannes");
assert_eq!(p.middle, "Diderik");
assert_eq!(p.last, "van der Waals");
assert_eq!(p.suffix, "");
```

Now on to something bigger and better.
