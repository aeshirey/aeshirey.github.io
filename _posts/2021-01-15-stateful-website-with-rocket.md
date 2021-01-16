---
layout: post
title:  "Stateful website with Rocket"
date:   2021-01-15 21:40:21 -0700
category: code
tags: [rust]
---

I wanted to try replacing my [`Flask`](https://flask.palletsprojects.com/en/1.1.x/) webserver for some local home projects with Rust. I decided to use [`Rocket`](https://rocket.rs/), but I didn't quite know how to keep some of the statefulness that I needed. Fortunately, in fewer than five minutes, I found [the answer in Rocket's docs: `State`](https://rocket.rs/v0.4/guide/state/).

Here's a simple webserver that hosts a page at `/hello/<name>/<age>` (eg, `/hello/dave/52`), keeps track of the most recent person to visit, and displays messages accordingly:

```rust
#![feature(proc_macro_hygiene, decl_macro)]
#[macro_use]
extern crate rocket;
use rocket::State;
use std::sync::Mutex;

#[get("/hello/<name>/<age>")]
fn hello(last_person: State<Mutex<(String, u8)>>, name: String, age: u8) -> String {
    // Acquire the lock mutably,
    let guard = &mut last_person.lock().unwrap();

    // get the name from the lock,
    let prev_name = guard.0.clone();

    // then update it. One deref gets the MutexGuard from its &mut; another gets the values from the Guard
    **guard = (name, age);

    // We've moved name & age into the guard, so we have to use that instead
    if prev_name.is_empty() {
        format!(
            "Hello, {} year old named {}! You're the first person to show up",
            guard.0, guard.1
        )
    } else {
        format!(
            "Hello, {} year old named {}! I just saw {}.",
            guard.0, guard.1, prev_name
        )
    }
}

fn main() {
    rocket::ignite()
        // Start with empty state:
        .manage(Mutex::new((String::new(), 0u8)))
        .mount("/", routes![hello])
        .launch();
}
```
