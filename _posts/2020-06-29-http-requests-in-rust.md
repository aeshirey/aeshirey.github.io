---
layout: post
title:  "HTTP requests in Rust"
date:   2020-06-29 01:56:48 -0700
category: code
tags: [rust]
---

I started my [`vesync-rs` library](https://github.com/aeshirey/vesync-rs) - which makes HTTP calls to the VeSync API - by using [`reqwest`](https://github.com/seanmonstar/reqwest):

```toml
[dependencies]
 reqwest = { version = "0.10", features = ["blocking", "json"] } 
```

Then I had both POST and GET requests, such as:

```rust
// POST request to the login route:
let client = reqwest::blocking::Client::new();
let response = client
    .post(&build_path("/vold/user/login"))
    .json(&request)
    .send()
    .map_err(|_e| ())?;

let account: AccountResponse = response.json().map_err(|_e| ())?;

// ...

// GET all known devices
let client = reqwest::blocking::Client::new();
let response = client
	.get(&build_path("/vold/user/devices"))
	.header("tk", &self.account.tk)
	.header("accountid", &self.account.accountID)
	.send()
	.map_err(|_e| ())?;

let devices: Vec<dto::Device> = response.json().map_err(|_e| ())?;
```

I discovered that [`attohttpc`](https://github.com/sbstp/attohttpc) is quite a bit smaller, which fits my project's needs better, so I switched my Cargo.toml:

```toml
[dependencies]
attohttpc = { version = "0.14.0", features = ["json"] }
```

And the POST and GET requests changed only slightly:

```rust
// POST request to the login route:
let response = attohttpc::post(&build_path("/vold/user/login"))
    .json(&request) // set the request body (json feature required)
    .map_err(|_e| ())?
    .send()
    .map_err(|_e| ())?;

let account: AccountResponse = response.json().map_err(|_e| ())?;

// GET all known devices
let response = attohttpc::get(&build_path("/vold/user/devices"))
	.header("tk", &self.account.tk)
	.header("accountid", &self.account.accountID)
	.send()
	.map_err(|_e| ())?;

let devices: Vec<dto::Device> = response.json().map_err(|_e| ())?;
```

The build went from 106 components to 62 components just with this one change. I believe Serde is responsible for the majority of those. I'm looking into [`nanoserde`](https://github.com/not-fl3/nanoserde), though its features aren't neary on-par with Serde.
