---
layout: post
title:  "Arc<Mutex<_>> in Rust"
date:   2020-12-23 09:43:33 -0700
category: code
tags: [rust]
---

A quick example of how to share data across threads in Rust using a [`Mutex`](https://doc.rust-lang.org/std/sync/struct.Mutex.html). First, a quick explanation:

Our data (`my_data`, below) is shared between multiple threads -- one thread might be updating it, another might want to read from it, yet another miht simultaneously try to update it from another entrypoint. We only have one copy of the data, so we use [mutual exclusion](https://en.wikipedia.org/wiki/Lock_(computer_science)) to allow exactly one entity to gain access to it at a time. But the mutex itself can't be safely accessed across multiple, so we use [`Arc` -- atomically reference counted](https://doc.rust-lang.org/std/sync/struct.Arc.html) -- to proctor access to the mutex.

Thus we have one copy of `my_data`, one Mutex wrapping it, and any number of fairly inexpensive Arcs\*. The entire code is here, and some brief explanation below:


```rust
use std::thread;
use std::{
    sync::{Arc, Mutex},
    time::Duration,
};

fn main() {
    // create my data, wrap it in a mutex, then add atomic reference couting
    let my_data = vec![1, 2, 3];
    let my_data = Mutex::new(my_data);
    let my_data = Arc::new(my_data);

    // spawn a thread that will update the values
    // a clone of our Arc will be moved into the thread
    let thread_arc = my_data.clone();
    let t1 = thread::spawn(move || {
        println!("Thread 1 attempting to acquire lock...");
        if let Ok(mut x) = thread_arc.lock() {
            println!("Thread 1 acquired lock");
            for num in x.iter_mut() {
                *num += 1;
            }

            // simulate some long-running work
            thread::sleep(Duration::from_millis(750));
        };
        println!("Thread 1 dropped lock");
    });

    let thread_arc = my_data.clone();
    let t2 = thread::spawn(move || {
        println!("Thread 2 attempting to acquire lock...");
        if let Ok(mut x) = thread_arc.lock() {
            println!("Thread 2 acquired lock");
            for num in x.iter_mut() {
                *num *= 2;
            }

            // simulate some long-running work
            thread::sleep(Duration::from_millis(1250));
        };
        println!("Thread 2 dropped lock");
    });

    t1.join().unwrap();
    t2.join().unwrap();

    let my_data = my_data.lock().unwrap();

    println!("Values are: {:?}", my_data);
}
```

Now for some explanation. First, we create data. Then we can [shadow](https://doc.rust-lang.org/rust-by-example/variable_bindings/scope.html) it for simplicity, wrapping the data first in a `Mutex`, then in an `Arc`. This can be done in one expression; here, I do it for clarity:

```rust
let my_data = vec![1, 2, 3];
let my_data = Mutex::new(my_data);
let my_data = Arc::new(my_data);
```

Next, we spawn two threads. Examining the first one, we first clone the `Arc<Mutex<Vec<i32>>>`:

```rust
// spawn a thread that will update the values
// a clone of our Arc will be moved into the thread
let thread_arc = my_data.clone();
```

To be clear, this clones the `Arc`; this gives us a reference to one and _only_ `Mutex` that wraps our one and only vector of data. When we spawn a new thread, we explicitly `move` this newly-cloned `Arc` into the thread. `thread_arc` is now no longer available in our main thread.

This new thread starts running by immediately attempting to acquire a lock on our data. It may or may not get it right away. If it does, then it will start modifying data; if not, it will block until it has access. Only *one* thread is able to access our data at a time.

```rust
let t1 = thread::spawn(move || {
    println!("Thread 1 attempting to acquire lock...");
    if let Ok(mut x) = thread_arc.lock() {
        println!("Thread 1 acquired lock");
        for num in x.iter_mut() {
            *num += 1;
        }

        // simulate some long-running work
        thread::sleep(Duration::from_millis(750));
    };
    println!("Thread 1 dropped lock");
});


When both threads are running, the main thread calls [`.join`](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html#method.join) to wait for them to finish. Here, we don't really care about the order in which `.join` is called becuase we don't want to do anything else until *both* have completed. These are blocking operations, so our main thread will wait until they're done. At that point, we acquire the lock, unwrap its `Result`, and we have the updated data. If we didn't call `.join`, our main thread would likely acquire the lock before the threads had time to start, and the program would exit before the threads had a chance to run.

```rust
t1.join().unwrap();
t2.join().unwrap();

let my_data = my_data.lock().unwrap();
```

One other note is that our two threads are basically started at the same time, so which one gets executed first is indeterminate. Therefore, our initial values of `[1, 2, 3]` might end up as `[3, 5, 7]` or `[4, 6, 8]`.

\* - Per [the `Arc` documentation](https://doc.rust-lang.org/std/sync/struct.Arc.html#thread-safety), "atomic operations are more expensive than ordinary memory accesses (`Rc`)", but using `Arc` overall isn't terribly expensive.
