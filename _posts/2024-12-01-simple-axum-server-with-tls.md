---
layout: post
title:  "Simple axum server with TLS"
date:   2024-12-01 11:57:09 -0700
category: code
tags: [rust]
---

I've begun moving from [`warp`](https://aeshirey.github.io/code/2022/01/11/understanding-warp.html) to `axum` with my Rust projects for various reasons. One project requires TLS, so I had to figure out the appropriate way to use certs in axum. Here's the simple version, based off of [axum's tls-rustls example](https://github.com/tokio-rs/axum/blob/main/examples/tls-rustls/src/main.rs). First, add some dependencies to your Cargo.toml:

```toml
[dependencies]
axum = "0.7"
axum-server = { version = "0.7", features = ["tls-rustls"] }
tokio = { version = "1.40.0", features = ["rt-multi-thread"] }
```

Then, we'll start with the basic version that does TLS:

```rust
use std::net::SocketAddr;

use axum::{routing::get, Router};

use axum_server::tls_rustls::RustlsConfig;

const HTTPS_PORT: u16 = 8443;

#[tokio::main]
async fn main() {
    let app = Router::new().route("/", get(root));

    let config = RustlsConfig::from_pem_file("cert3.pem", "privkey3.pem")
        .await
        .unwrap();

    let addr = SocketAddr::from(([0, 0, 0, 0], HTTPS_PORT));

    axum_server::bind_rustls(addr, config)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn root() -> &'static str {
    "Hello, World!"
}
```

The only real important parts here are the use of a specific port for HTTPS (see below) and the use of the [`from_pem_file`](https://docs.rs/axum-server/latest/axum_server/tls_rustls/struct.RustlsConfig.html#method.from_pem_file) function. (There are both [`tls_rustls`](https://docs.rs/axum-server/latest/axum_server/tls_rustls/index.html) and [`tls_openssl`](https://docs.rs/axum-server/latest/axum_server/tls_openssl/index.html) modules for your TLS implementation of choice.)

One thing you might want is an HTTP-to-HTTPS redirect: if a user hits your server with the `http` scheme, you can automatically redirect to an `https` endpoint. This requires a few more imports, a function to do the redirect, and a spawned task. A complete, updated version of the above code:


```rust
use std::net::SocketAddr;

use axum::{
    extract::Host,
    handler::HandlerWithoutStateExt,
    http::{StatusCode, Uri},
    response::Redirect,
    routing::get,
    BoxError, Router,
};

use axum_server::tls_rustls::RustlsConfig;

const HTTP_PORT: u16 = 8080;
const HTTPS_PORT: u16 = 8443;

#[tokio::main]
async fn main() {
    let app = Router::new().route("/", get(root));

    tokio::spawn(redirect_http_to_https());

    let config = RustlsConfig::from_pem_file("cert3.pem", "privkey3.pem")
        .await
        .unwrap();

    let addr = SocketAddr::from(([0, 0, 0, 0], HTTPS_PORT));

    axum_server::bind_rustls(addr, config)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn root() -> &'static str {
    "Hello, World!"
}

async fn redirect_http_to_https() {
    fn make_https(host: String, uri: Uri) -> Result<Uri, BoxError> {
        let mut parts = uri.into_parts();

        parts.scheme = Some(axum::http::uri::Scheme::HTTPS);

        if parts.path_and_query.is_none() {
            parts.path_and_query = Some("/".parse().unwrap());
        }

        let https_host = host.replace(&HTTP_PORT.to_string(), &HTTPS_PORT.to_string());
        parts.authority = Some(https_host.parse()?);

        Ok(Uri::from_parts(parts)?)
    }

    let redirect = move |Host(host): Host, uri: Uri| async move {
        match make_https(host, uri) {
            Ok(uri) => Ok(Redirect::permanent(&uri.to_string())),
            Err(_) => Err(StatusCode::BAD_REQUEST),
        }
    };

    let addr = SocketAddr::from(([127, 0, 0, 1], HTTP_PORT));
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();

    axum::serve(listener, redirect.into_make_service())
        .await
        .unwrap();
}
```

Note that HTTP and HTTPS _must_ use different ports, else you'll get an "Address already in use" error when trying to bind multiple schemes.
