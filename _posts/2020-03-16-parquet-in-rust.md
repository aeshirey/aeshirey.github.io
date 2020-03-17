---
layout: post
title:  "Parquet in Rust"
date:   2020-03-16 23:00:07 -0700
category: code
tags: [rust, python]
---

One of my projects at work has lead me to dig into processing some large data in Parquet format, so I spent some time figuring out how to do so in Rust using [parquet-rs](https://github.com/sunchao/parquet-rs). Below is a simple example of how to create data in Python and read it in with Rust. My current use case has little more than very simple Parquet -- no concern with indexes, partitioning, etc.; just simple row-wise processing of compressed, structured data.

## Create Dataset
First, I created a simple dataset in Python+Pandas:

```python
import pandas as pd

people = { 'name': ['Alice', 'Bob', 'Charlie', 'Dave'],
        'age': [35, 32, 41, 27],
        'height': [ 178.6, 175.3, 177, 175 ],
        'languages': [['English', 'French'], ['English'], [], ['Python', 'Rust']],
        'is_employed': [True, True, False, True],
        }

df = pd.DataFrame(people)

df.to_parquet('my_dataset.parquet')
```

This dataset looks like this from Python:

```none
>>> df
      name  age  height          languages  is_employed
0    Alice   35   178.6  [English, French]         True
1      Bob   32   175.3          [English]         True
2  Charlie   41   177.0                 []        False
3     Dave   27   175.0     [Python, Rust]         True
```

## Setup Rust Project
Create a new Rust project with `cargo new parquet_test`. parquet-rs takes a dependency on nightly, so specify the override: `rustup override set nightly`.

Add to your Cargo.toml file a dependency of `parquet = "0.16"`.

## Rust code


```rust
use std::fs::File;

extern crate parquet;
use parquet::file::reader::SerializedFileReader;
use parquet::record::{ListAccessor, RowAccessor};

fn main() {
    let filename = "my_dataset.parquet";

    let fh = File::open(filename).unwrap();
    let reader: SerializedFileReader<File> = SerializedFileReader::new(fh).unwrap();

    let mut lines = 0;

    for row in reader.into_iter() {
        lines += 1;
        println!("Row {}", lines);

        let name = row.get_string(0).unwrap();
        let age = row.get_long(1).unwrap();

        // NB: Trying to read in the column with get_long or get_float will fail; it must be get_double
        let height = row.get_double(2).unwrap();

        let languages: &parquet::record::List = row.get_list(3).unwrap();

        let is_employed = row.get_bool(4).unwrap();

        println!(
            "    Name={}, age={}, height={}, is_employed={}",
            name, age, height, is_employed
        );
        print!("    Languages: ");
        if languages.len() == 0 {
            println!("(none)");
        } else {
            for i in 0..languages.len() {
                let lang = languages.get_string(i).unwrap();
                print!("{}, ", lang);
            }
        }
        println!("\n---");
    }
}
```
