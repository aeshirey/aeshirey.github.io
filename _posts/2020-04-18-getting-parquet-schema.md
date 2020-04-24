---
layout: post
title:  "Parquet in Rust: Reading the Schema"
date:   2020-04-18 08:14:00 -0700
category: code
tags: [rust]
---

Following-up on [my previous post about reading Parquet files in Rust](https://aeshirey.github.io/code/2020/03/17/parquet-in-rust.html), I spent some time looking through the [`parquet` crate's documentation](https://docs.rs/parquet/0.16.0/parquet/index.html) for how to get the schema. Once I distilled it down, it's actually a lot simpler than I expected:

```rust
use std::fs::File;
extern crate parquet;
use parquet::file::reader::{FileReader, SerializedFileReader};
use parquet::schema::types::Type;

fn main() -> Result<(), std::io::Error> {
    let filename = "my_dataset.parquet";
    let fh = File::open(filename)?;
    let reader: SerializedFileReader<File> = SerializedFileReader::new(fh)?;

    let schema: &parquet::schema::types::Type = reader.metadata().file_metadata().schema();

    // recursively display the schema (because a type can be a list of other types)
    display(schema, 0);

    Ok(())
}

fn display(schema: &Type, depth: usize) {
    let name = schema.name();
    let indent = " ".repeat(4 * depth);
    match schema {
        Type::PrimitiveType { physical_type, .. } => println!("{}{} : {}", indent, name, physical_type),
        Type::GroupType { .. } => println!("{}{} is a list type", indent, name),
    }

    // this type is a list of other types
    if schema.is_group() {
        for column in schema.get_fields() {
            display(column, depth + 1);
        }
    }
}
```

Running this code generates the following output for the sample dataset:

```
schema is a list type
    name : BYTE_ARRAY
    age : INT64
    height : DOUBLE
    languages is a list type
        list is a list type
            item : BYTE_ARRAY
    is_employed : BOOLEAN
```
