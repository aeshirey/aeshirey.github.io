---
layout: post
title:  "Of course, sir, it's a cheese shop!"
date:   2020-03-11 11:21:07 -0700
category: code
tags: [rust, python]
---

I've become quite interested in Rust lately and have been playing around with it a bit in my free time. My day-to-day work is currently doing some pattern mining in Python with Pandas and Dask. Since some of the tests I've done on our datasets are taking in the 1-3 minute range (even on an AKS cluster of several nodes), I thought I'd see how performant I could get Rust. Using [PyO3 Rust bindings for Python](https://github.com/PyO3/pyo3/), I was able to get a blazing fast (~10 seconds) analog - on a single machine.

Learning Rust is and will be a journey for me, being an engineer who typically deals with higher-level languages. So as part of my learning process, I have started putting together some examples of how PyO3 works: the [CheeseShop](https://github.com/aeshirey/CheeseShop).

A trivial example of the Rust code one might implement:

```rust
#[pyfunction]
fn do_something_in_rust(py: Python, obj: &PyAny) -> PyResult<()> {
    let strval: Result<&str, PyErr> = value.extract();
    if let Ok(strval) = strval {
        println!("Received string value of \"{}\"", strval);
    } else {
        // Other types of .extract() may be done, too.
        println!("Received some other value: {:?}", value);
    }

    Ok(())
}
```

This can then be called (after loading your module) in Python:

```python
do_something_in_rust("Hello, Mr. Polly Parrot!");
do_something_in_rust(1.618034);
```
