---
layout: post
title:  "Understanding warp"
date:   2022-01-11 12:59:12 -0700
category: code
tags: [rust]
---

[warp](https://docs.rs/warp/latest/warp/index.html) bills itself as "a super-easy ... web server framework." And while I am (happily) using it in a production service at work, I didn't find it super easy to setup. I kind of stumbled into a successful implementation for my service. Because I wanted to better understand how to compose different route handlers, I dived into how it works. This post covers those very basics.

As usual, let's start with the dependencies. Our webserver should run asynchronously for maximum throughput, so we'll use `tokio` and `futures`, and of course the `warp` crate:

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
futures = "0.3"
warp = "0.3"
```

Warp uses the concept of composable request [`Filter`s](https://docs.rs/warp/latest/warp/trait.Filter.html): components that match requests, extract data from them (URI components, query parameters, request bodes, etc.), and chain together (and/or).

## Welcome

To start, we'll make our `main` function asynchronous and add a route that matches the root of the server and prints a welcome message:

```rust
#[tokio::main]
async fn main() {
    use warp::Filter;
    let index = warp::path::end().map(|| "Welcome!");

    let routes = index;
    warp::serve(routes).run(([0, 0, 0, 0], 3000)).await;
}
```

`warp::path::end` is used to identify that the path handling is complete, and since it's not chained with any previous components, it effectively matches "/". (Think of it like the regular expression `"/$"`.) We then `.map` the input request to the `&str` output.

In this post, I'm using the convention of serving up a `routes` value; in this first example, we're only serving a single route.

Very unsurprisingly, if you run this project and go to http://127.0.0.1:3000/, you will see the welcome text.

## Hello
This first request isn't particularly interesting or transparent, so let's handle an input path such as `/hello/adam` as a way to say hello to the user, and its code will be added as its own function.

```rust
async fn main() {
    use warp::{path, Filter};
    let index = warp::path::end().map(|| "Welcome!");

    let hello = path!("hello" / String).then(handle_hello);

    let routes = index.or(hello);
    warp::serve(routes).run(([0, 0, 0, 0], 3000)).await;
}

async fn handle_hello(name: String) -> impl warp::Reply {
    format!("Hello, {}", name)
}
```

There are several changes here:

* `hello` is defined using the [`warp::path!`](https://docs.rs/warp/latest/warp/macro.path.html) macro which adds convenience for declaring URI path components and arguments. `path!("hello" / String)` declares that we're handling a path that starts with the literal `hello` then some String argument.
* We augment our handled routes by handling any request that matches the root (via `index`) _or_ any request that matches the `hello` handler. When a request comes in, warp will first check whether `index` handles it; if not, it will check if `hello` handles it.
* The asynchronous `handle_hello` function accepts the provided argument and returns some type that implements `Reply`. Note that under the hood, this async function ends up returning a `Future`, but this is transparent to us.
* To use an async function, we compose our path with `.then`; unintuitively, if `handle_hello` was synchronous, we'd use `.map` instead.

In addition to the welcome message at the root, you can now go to http://127.0.0.1:3000/hello/adam to see `"Hello, adam"`.

## Goodbye - like hello, but different
The `goodbye` handler will be very similar to `hello` but with some minor tweaks. First, we might want to either return 200 OK (which is the default) _or_ some alternate status code. The new handler will conditionally return an error code for certain kinds of input:

```rust
use std::convert::Infallible;
use warp::{hyper::StatusCode, reply, Reply};

#[tokio::main]
async fn main() {
    // ...

    let goodbye = warp::path("goodbye")
        .and(warp::path::param())
        .and(warp::path::end())
        .and_then(handle_goodbye);

    // ...
}

async fn handle_goodbye(name: String) -> Result<impl Reply, Infallible> {
    if name == "earl" {
        Ok(reply::with_status(
            "Earl Grey is a tea".to_string(),
            StatusCode::IM_A_TEAPOT,
        ))
    } else {
        Ok(reply::with_status(
            format!("Goodbye, {}", name),
            StatusCode::OK,
        ))
    }
}
```

Declaring `goodbye` is now using the explicit warp Filters `path`, `param`, and `end`. This is very much like `path!` did for `hello`. Like many things in Rust, the type for the `param` is inferred by virtue of the function we're calling. Note that both `handle_hello` and `handle_goodbye` use _owned_ values (ie, String instead of &str), which is required for async functions for reasons outside the scope of this post.

The function `handle_goodbye` now returns a `Result<_, Infallible>`. This is to say, this function cannot fail (all code paths _must_ return `Ok`) but does return a `Result`. There are times in which you must return a `Result`, and if the function never fails, we can use `Infallable` as the error type. Becausue this function returns a result, we switch `goodbye` from using `.then` to `.and_then` -- also unintuitive, IMO.

Finally, this function uses the `reply::with_status` function to return two different replies and statuses depending on some condition (here, the value of `name`). But both branches will return a specific concrete type (`warp::reply::WithStatus`), so we still use `impl Reply`.

## Logins are more complicated
All three routes are currently infallible -- if an HTTP request matches the path for a route, warp _will_ respond to it. Usually it's with a 200 OK, but sometimes with 418 IM_A_TEAPOT. And the responses all contain a text body. But what if we want to redirect to another page? Or what if we start handling a request, decide that the designated function isn't equipped to handle it, and want another function to take over? This is where we make use of `Rejection`s. First, let's setup a `login` route:

```rust
let login = warp::path("login")
    .and(warp::path::param())
    .and(warp::path::end())
    .and_then(handle_login);

let routes = index.or(hello).or(goodbye).or(login);
```

(We're still just using the request path, such as `/login/adam`, for simplicity.)

The handling function is now no longer fallible and can reject the request (which is to say that it will allow another handler to potentially pick it up). Let's assume there are a few users that we don't want to login: `agent_smith` and `neo`:

```rust
async fn handle_login(name: String) -> Result<String, warp::Rejection> {
    if name == "agent_smith" {
        todo!()
    } else if name == "neo" {
        todo!()
    } else {
        Ok(format!("You are now logged in as '{}'", name))
    }
}
```

(This function's happy path returns a `String` instead of `impl Reply` only to show that it's possible to declare it that way. `String` _does_ implement `Reply`, so this is functionally identical.)

What should we do for these users? [`warp::reject`](https://docs.rs/warp/latest/warp/reject/index.html) provides a `not_found` function that will rejet a request. For Agent Smith, let's use that:

```rust
    if name == "agent_smith" {
        Err(warp::reject::not_found())
    } else if name == "neo" {
        todo!()
    }
```

But 'not found' isn't particularly descriptive, and it doesn't give us much control over how the rejection is subsequently handled. We can create our own types that implements `Debug` and `Reject`, then we can return this as a custom rejection:

```rust
#[derive(Debug)]
struct Neo;
impl warp::reject::Reject for Neo {}

async fn handle_login(name: String) -> Result<String, warp::Rejection> {
    if name == "agent_smith" {
        Err(warp::reject::not_found())
    } else if name == "neo" {
        Err(warp::reject::custom(Neo))
    } else {
        Ok(format!("You are now logged in as '{}'", name))
    }
}
```

Now we have three different types of responses to our three different logins:

* http://127.0.0.1:3000/login/adam will return 200 `"You are now logged in as 'adam'"`
* http://127.0.0.1:3000/login/agent_smith will return 404
* http://127.0.0.1:3000/login/neo will return 500 `"Unhandled rejection: Neo"`

But how can we make use of these rejected requests?

## Setting a fall-through handler
The first and simplest way to handle these rejected requests is to add another handler that will match them, thus giving them a chance to be handled in another way.

```rust
let fallthrough = warp::any().map(|| "All other requests here");
let routes = index.or(hello).or(goodbye).or(login).or(fallthrough);
```

`.any` matches all requests. Since `fallthrough` comes after `login` in our route handling, if the latter rejects the request, the former will pick it up. Thus, `/login/adam` logs us in while the other two will now return 200 `"All other requests here"`.

This is pretty rudimentary, so let's try something more complex.

## Handling rejections
A warp `Rejection` can be recovered with [`.recover`](https://docs.rs/warp/latest/warp/trait.Filter.html#method.recover). If a request is rejected, it is passed to the recovery function which can then do something with it. (And that something might itself be another rejection.)

```rust
#[tokio::main]
async fn main() {
    // ...

    let routes = index
        .or(hello)
        .or(goodbye)
        .or(login)
        .recover(handle_rejection);

    // ...
}

async fn handle_rejection(err: warp::Rejection) -> Result<Box<dyn Reply>, warp::Rejection> {
    if err.is_not_found() {
        Ok(Box::new(warp::redirect(warp::hyper::Uri::from_static("/"))))
    } else if err.find::<Neo>().is_some() {
        Ok(Box::new(reply::with_status(
            "Follow the white rabbit",
            StatusCode::UNAUTHORIZED,
        )))
    } else {
        Ok(Box::new(reply::with_status(
            r#"¯\_(ツ)_/¯"#,
            StatusCode::INTERNAL_SERVER_ERROR,
        )))
    }
}
```

We are rejecting `/login/agent_smith` with a not found request, so those can be handled by checking `err.is_not_found`. In that case, we'll redirect to the root of our server. And the the `Neo` rejection type is handled using `err.find::<>`. In that case, we construct a 401 response with the specified message. All other rejections -- which _shouldn't_ be possible right now -- are gracefully handled with a 500. Note that this means the request can't fall through to any other recovery function should we add one later on.

You'll also note that this function doesn't return an `impl Reply` but a `Box<dyn Reply>`. This is because we now no longer have one concrete type being returned but two: the `WithStatus` as before but also whatever `redirect` returns, which in this case is a `warp::reply::WithHeader`. Thus we have to box the return type.


# The entire example
Here's the code of this entire sample, combined and with comments:

```rust
use std::convert::Infallible;
use warp::{hyper::StatusCode, path, reply, Filter, Reply};

#[tokio::main]
async fn main() {
    // The index (/) of our webserver shows a simple message.
    let index = warp::path::end().map(|| "Welcome!");

    // A simple GET route declaration using the `path!` macro: we can
    // declare the route ("hello") and the expected parameter type (String)
    let hello = path!("hello" / String).then(handle_hello);

    // The same idea as above but with the individual warp components.
    // Additionally, `goodbye` can return error codes for 'bad' input.
    let goodbye = warp::path("goodbye")
        .and(warp::path::param())
        .and(warp::path::end())
        .and_then(handle_goodbye);

    //
    let login = warp::path("login")
        .and(warp::path::param())
        .and(warp::path::end())
        .and_then(handle_login);

    // If we decide to use a fallthrough request handler, this just 
    // catches everything in a rather uninteresting way.
    let fallthrough = warp::any().map(|| "All other requests here");

    let routes = index
        .or(hello)
        .or(goodbye)
        .or(login)
        //.or(fallthrough) // not used, and it CAN'T be used in conjunction with .recover
        .recover(handle_rejection);

    warp::serve(routes).run(([0, 0, 0, 0], 3000)).await;
}

/// This function is infallible, so we can simply return an impl Reply.
/// To use it, we make use of [warp::Filter::then], which expects a Future.
async fn handle_hello(name: String) -> impl warp::Reply {
    format!("Hello, {}", name)
}

/// This function is also in fallible, but for demonstration purposes, we'll return a `Result<_, Infallible>`.
/// Because of this, we use [warp::Filter::and_then], which is normally for fallible async functions.
///
/// Unrelated to fallibility, this function may return different error codes depending on the input.
/// We rewrite the response with a [warp::reply::StatusCode], so the impl Reply is a [warp::reply::WithStatus].
/// And because [`impl Trait`](https://doc.rust-lang.org/rust-by-example/trait/impl_trait.html) returns a concrete
/// type, the two branches here must be the same type -- that is, we can't return a String on one
/// side and a WithStatus on the other.
async fn handle_goodbye(name: String) -> Result<impl Reply, Infallible> {
    if name == "earl" {
        Ok(reply::with_status(
            "Earl Grey is a tea".to_string(),
            StatusCode::IM_A_TEAPOT,
        ))
    } else {
        Ok(reply::with_status(
            format!("Goodbye, {}", name),
            StatusCode::OK,
        ))
    }
}

#[derive(Debug)]
struct Neo;
impl warp::reject::Reject for Neo {}

/// On login, we might reject certain inputs and allow some other request handler
/// to take over.
/// 
/// There are two types of rejections here: for `"agent_smith"`, we return a 404,
/// while for `"neo"`, we'll return the custom rejection defined above.
async fn handle_login(name: String) -> Result<impl Reply, warp::Rejection> {
    if name == "agent_smith" {
        Err(warp::reject::not_found())
    } else if name == "neo" {
        Err(warp::reject::custom(Neo))
    } else {
        Ok(format!("You are now logged in as '{}'", name))
    }
}

/// When specifynig the routes we want to serve, we can `.recover` them with this function.
/// Any Rejection that comes before the recovery will be send here, and we can handle it
/// or send it back for yet another later recovery.
/// 
/// Additionally, yet not required, this function returns different kinds of replies, so
/// the return type is `Box<dyn Reply>`, and each concrete type is boxed accordingly.
async fn handle_rejection(err: warp::Rejection) -> Result<Box<dyn Reply>, warp::Rejection> {
    if err.is_not_found() {
        Ok(Box::new(warp::redirect(warp::hyper::Uri::from_static("/"))))
    } else if err.find::<Neo>().is_some() {
        Ok(Box::new(reply::with_status(
            "Follow the white rabbit",
            StatusCode::UNAUTHORIZED,
        )))
    } else {
        Ok(Box::new(reply::with_status(
            r#"¯\_(ツ)_/¯"#,
            StatusCode::INTERNAL_SERVER_ERROR,
        )))
    }
}
```