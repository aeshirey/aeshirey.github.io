---
layout: post
title:  "Rayon thread pools in Rust"
date:   2023-02-10 10:02:17 -0700
category: code
tags: [rust]
---

[`rayon`](https://docs.rs/rayon/latest/rayon/index.html) provides an incredibly simple [work stealing](https://en.wikipedia.org/wiki/Work_stealing) framework that, in my experience, requires only two lines of code that can dramatically improve processing throughput. To use, you'll need to add it to your Cargo.toml with `cargo add rayon`.

Consider some function that does some intensive work:

```rust
/// Do some number of iterations of work
fn do_work(worker: usize, iterations: usize) {
    println!("Worker {worker} doing work");

    if iterations > 0 {
        // simulate long-running work with 'sleep'
        // we might do different kinds of work depending on the worker,
        // eg, open a different file of input.
        std::thread::sleep(std::time::Duration::from_secs(1));
        do_work(worker, iterations - 1)
    }
}
```

Doing this serially might look like this:

```rust
const NUM_WORKERS: usize = 5;
const NUM_ITERATIONS: usize = 4;
fn main() {
    let s = std::time::Instant::now();
    (1..=NUM_WORKERS).for_each(|worker| do_work(worker, NUM_ITERATIONS));
    println!("Work took {:?}", s.elapsed());
}
```

This produces the very boring output:

```
Worker 1 doing work
Worker 1 doing work
Worker 1 doing work
Worker 1 doing work
Worker 1 doing work
Worker 2 doing work
Worker 2 doing work
Worker 2 doing work
Worker 2 doing work
Worker 2 doing work
Worker 3 doing work
Worker 3 doing work
Worker 3 doing work
Worker 3 doing work
Worker 3 doing work
Worker 4 doing work
Worker 4 doing work
Worker 4 doing work
Worker 4 doing work
Worker 4 doing work
Worker 5 doing work
Worker 5 doing work
Worker 5 doing work
Worker 5 doing work
Worker 5 doing work
Work took 20.007646351s
```

This might be rather inefficient, especially if we have many CPU cores sitting idle. Instead, we can use rayon and use one of the `*par_iter` variations:

```rust
use rayon::prelude::*; // this is new
fn main() {
    let s = std::time::Instant::now();
    (1..=NUM_WORKERS)
        .into_par_iter() // and this is new
        .for_each(|worker| do_work(worker, NUM_ITERATIONS));
    println!("Work took {:?}", s.elapsed());
}
```

This is much faster, as it will parallelize the work according to [the number of CPUs available](https://github.com/rayon-rs/rayon/blob/master/FAQ.md#how-many-threads-will-rayon-spawn):

```
Worker 1 doing work
Worker 3 doing work
Worker 2 doing work
Worker 4 doing work
Worker 1 doing work
Worker 3 doing work
Worker 2 doing work
Worker 4 doing work
Worker 1 doing work
Worker 3 doing work
Worker 2 doing work
Worker 4 doing work
Worker 1 doing work
Worker 3 doing work
Worker 2 doing work
Worker 4 doing work
Worker 1 doing work
Worker 5 doing work
Worker 3 doing work
Worker 2 doing work
Worker 4 doing work
Worker 5 doing work
Worker 5 doing work
Worker 5 doing work
Worker 5 doing work
Work took 8.011677642s
```

Two things to note here:

1. Because this is now multithreading our work, the order of individual steps -- in this case, 1, 3, 2, then 4 -- isn't exactly what we expect.
2. We had five units of work (ie, five workers), but Rayon parallelized across four threads. In other words, it ran steps 1-4 in parallel, but step 5 ran after the others. This may be sub-optimal, so you can use a [`ThreadPool`](https://docs.rs/rayon/1.6.1/rayon/struct.ThreadPool.html) to configure the number of threads:

```rust
fn main() {
    let s = std::time::Instant::now();
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(NUM_WORKERS) // use one thread per work slice
        .build()
        .unwrap();
    
    pool.install(|| {
        (1..=NUM_WORKERS)
            .into_par_iter()
            .for_each(|worker| do_work(worker, NUM_ITERATIONS));
    });
    println!("Work took {:?}", s.elapsed());
}
```

Alternately, you may want to limit your parallelism to leave compute available to other tasks:

```rust
fn main() {
    let s = std::time::Instant::now();
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(2) // use only two threads
        .build()
        .unwrap();

    pool.install(|| {
        (1..=NUM_WORKERS)
            .into_par_iter()
            .for_each(|worker| do_work(worker, NUM_ITERATIONS));
    });
    println!("Work took {:?}", s.elapsed());
}
```

```
Worker 1 doing work
Worker 3 doing work
Worker 2 doing work
Worker 4 doing work
Worker 5 doing work
Worker 1 doing work
Worker 3 doing work
Worker 4 doing work
Worker 2 doing work
Worker 5 doing work
Worker 1 doing work
Worker 3 doing work
Worker 4 doing work
Worker 2 doing work
Worker 5 doing work
Worker 1 doing work
Worker 3 doing work
Worker 4 doing work
Worker 2 doing work
Worker 5 doing work
Worker 1 doing work
Worker 3 doing work
Worker 4 doing work
Worker 2 doing work
Worker 5 doing work
Work took 4.002877261s
```
