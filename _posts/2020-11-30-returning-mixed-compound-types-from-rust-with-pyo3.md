---
layout: post
title:  "Returning mixed compound types from Rust with PyO3"
date:   2020-11-30 22:26:53 -0700
category: code
tags: [rust, python, pyo3]
---

With [PyO3](https://github.com/PyO3/pyo3/), it's very easy to return scalar values from a function: simply declare a Rust function with the `#[pyfunction]` attribute and everything works:

```rust
#[pyfunction]
fn is_even(n: u32) -> bool {
   n % 2 == 0
}
```

This extends to tuples, lists (Rust `Vec`), and dicts (rust `HashMap`) similarly easily:

```rust
#[pyfunction]
fn rust_dict() -> HashMap<String, u32> {
    let mut hm = HashMap::new();

    hm.insert("one".to_string(), 1);
    hm.insert("two".to_string(), 2);

    hm
}
```

But to return a compound type with mixed values -- say, a list of strings, ints, and bools -- you have to explicitly convert each value to a `PyObject`. This lets Rust type the data structure properly.


```rust
use pyo3::types::{PyTuple, PyList, PyDict};

#[pyfunction]
fn returns_list(py: Python) -> &PyList {
    let items = vec![
        1.to_object(py),
        2.0f32.to_object(py),
        "three".to_object(py),
        true.to_object(py)
    ];

    PyList::new(py, items)
}

#[pyfunction]
fn returns_dict(py: Python) -> &PyDict {
    let items = vec![
        (9.to_object(py), 1.to_object(py)),
        ("two".to_object(py), 2.0f32.to_object(py)),
        (true.to_object(py), "three".to_object(py)),
        ("zzz".to_object(py), true.to_object(py))
    ].to_object(py);

    PyDict::from_sequence(py, items).unwrap()
}


#[pyfunction]
fn returns_obj(py: Python, selector: u32) -> PyObject {
    match selector % 4 {
        // [1, 2.0, 'three', True]
        0 => returns_list(py).to_object(py),

        // {9: 1, 'two': 2.0, True: 'three', 'zzz': True, 'none': None}
        1 => {
            let mut d = returns_dict(py);
            d.set_item("none", py.None());
            
            d.to_object(py)
        }

        // 'hello'
        2 => "hello".to_object(py),

        // (1, 'two', 3.0)
        3 => PyTuple::new(py, vec![
                          1.to_object(py),
                          "two".to_object(py),
                          3.0.to_object(py),
        ]).to_object(py),
        _ => unreachable!()
    }
}
```
