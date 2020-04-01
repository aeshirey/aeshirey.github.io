---
layout: post
title:  "Tests and PyO3"
date:   2020-03-31 22:40:07 -0700
category: code
tags: [python, rust]
---

I recently discovered that when using [PyO3](https://github.com/PyO3/PyO3)'s getters and setters for a `pyclass`, `cargo test` is broken. Consider the following example lib.rs:

```rust
#[pyclass]
struct MyStruct {
    #[pyo3(get, set)] // Makes `i` readable/writable in Python
    i: u32,
}

#[pymethods]
impl MyStruct {
    #[new]
    fn new(i: u32) -> Self {
        MyStruct { i: i + 1 }
    }
}

#[pymodule]
fn tests_and_getters(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MyStruct>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn i_plus_1() {
        let my_struct = MyStruct::new(123);
        assert_eq!(my_struct.i, 124);
    }
}
```

Creating an instance of `MyStruct` should set its value of `i` to the passed value plus one. So how do we test it? We should be able to `i_plus_1` with `cargo test`. What we find instead is the following error:

```none
error: linking with `cc` failed: exit code: 1
  |
  = note: "cc" "-Wl,--as-needed" "-Wl,-z,noexecstack" "-m64" "-L" "...
...
...
= note: /home/user/rust/gettertest/target/debug/deps/tests_and_getters-94c0ceb1fd2ab0ef.hra3dhvd2c210xh.rcgu.o: In function `pyo3::err::PyErr::restore':
      /home/user/.cargo/registry/src/github.com-1ecc6299db9ec823/pyo3-0.9.1/src/err.rs:345: undefined reference to `PyErr_Restore'
      /home/user/rust/gettertest/target/debug/deps/libpyo3-a88cb910efc8a664.rlib(pyo3-a88cb910efc8
      ...
```

Note that this error doesn't occur if we comment out the getter and setter attributes. In other words, this will let us run `cargo test` without a problem:

```rust
#[pyclass]
struct MyStruct {
    // #[pyo3(get, set)] // Makes `i` readable/writable in Python
    i: u32,
}
```

Since I'm starting to use PyO3 in a work project, I'd really like to include tests in my code without giving up using getters/setters. Fortunately, there's a workaround. By default, we might set `features = ["extension-module"]` in our Cargo.toml. Instead, change this to:

```toml
[dependencies.pyo3]
version = "0.9.1"

# No longer need this:
#features = ["extension-module"]

# But we want these two:
extension-module = ["extension-module"]
default = ["extension-module"]
```

Then - just for testing - disable default features:

```bash
cargo test --no-default-features
```
