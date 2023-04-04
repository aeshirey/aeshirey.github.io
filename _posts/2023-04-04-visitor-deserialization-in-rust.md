---
layout: post
title:  "Visitor Deserialization in Rust"
date:   2023-04-04 08:21:06 -0700
category: code
tags: [rust]
---

Consider the following input JSON:

```json
{
   "documents": [
      { "foo": 1 },
      { "baz": true },
      { "bar": null }
   ],
   "journal": { "timestamp": "2023-04-04T08:28:00" }
}
```

If we assume that each inner 'document' should be simply treated as an arbitrary JSON [`Value`](https://docs.rs/serde_json/latest/serde_json/enum.Value.html), we can model and read our input as:

```rust
#[derive(Deserialize, Debug)]
struct MyData {
    documents: Vec<Value>,
    journal: Value,
}

fn main() {
    let json = std::fs::read_to_string("input.json").unwrap();
    let mydata: MyData = serde_json::from_str(&json).unwrap();
    println!("{mydata:?}");
}
```

But what if we only need a subset of 'documents' and/or need to process each into something else, and they are exceedingly large? This would cause significant memory overhead that we want to avoid. One possibility is to roll your own string reading mechanism, trying to figure out when one document starts and ends, then parsing only _that_ string. This becomes a bit cumbersome, but worse still is that it may be error prone when trying to deal with the arbitrary `journal` value: how do we know if we've finished reading the last document and have arrived at the journal? What if a document legitimately contains a `"journal"` key?

Fortunately, [`serde`](https://docs.rs/serde/latest/serde/) contains the capability to do custom serialization and deserialization _and_ to use a [visitor pattern](https://docs.rs/serde/latest/serde/de/trait.Visitor.html). We can use this approach to handle each document in succession. To do so, we'll create a new type that represents our documents:

```rust
#[derive(Debug)]
struct Documents(Vec<Value>);

#[derive(Deserialize, Debug)]
struct MyData {
    documents: Documents,
    journal: Value,
}
```

Structurally, this is the same as before, but it allows us to insert our own, manual deserialization step -- note that `MyData` implements `Deserialize` but `Documents` doesn't. The deserialization implementation stub looks like this:

```rust
impl<'de> Deserialize<'de> for Documents {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        todo!()
    }
}
```

Before implementing this part, we'll create the visitor. First, the type that will know how to deserialize our documents:

```rust
struct DocumentVisitor;
```

Note that `DocumentVisitor` itself doesn't collect `Value`s -- it just _knows how_ to deserialize them. Serde's visitor pattern has an associated type that will be the (collected) result of deserialization. This output is what we will have filtered and/or processed from each raw JSON value from input. Here's the stub for the visitor:

```rust
impl<'de> serde::de::Visitor<'de> for DocumentVisitor {
    type Value;

    fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
        todo!()
    }
}
```

[`expecting`](https://docs.rs/serde/latest/serde/de/trait.Visitor.html#tymethod.expecting) is a required method that:

> [Formats] a message stating what data this Visitor expects to receive. ... The message should complete the sentence "This Visitor expects to receive ...",

Because our visitor expects a list of documents, we'll say that:

```rust
fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
    write!(formatter, "a list of JSON values")
}
```

Also because we're expecting a list (or _sequence_) of items, we'll override the [`visit_seq` method](https://docs.rs/serde/latest/serde/de/trait.Visitor.html#method.visit_seq). We also set the [required associated type, `Value`](https://docs.rs/serde/latest/serde/de/trait.Visitor.html#associatedtype.Value), indicating what kind of value this visitor will be returning. (Note that here, the associated type `Value` is not the same as `serde_json::Value`. The former is what we'll be telling serde that we'll return, which is a `Vec<Value>`. The latter is specific to JSON data.) In `visit_seq`, we'll repeatedly call `seq.next_element()`, propagating up any errors that serde gives us. For now, we'll just push each item onto a vector that we'll return:

```rust
    type Value = Vec<Value>;

    fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
    where
        A: serde::de::SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(item) = seq.next_element()? {
            println!("Read item='{item}'");
            values.push(item)
        }
        Ok(values)
    }
```

That completes the visitor, and we can now implement `Deserialize for Documents`. We'll instantiate a visitor, which is passed to the [deserializer's `deserialize_seq` method](https://docs.rs/serde/latest/serde/de/trait.Deserializer.html#tymethod.deserialize_seq):

```rust
impl<'de> Deserialize<'de> for Documents {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let visitor = DocumentVisitor;
        let docs = deserializer.deserialize_seq(visitor)?;
        Ok(Documents(docs))
    }
}
```

Note that by passing a `DocumentVisitor` to the deserializer, serde knows that it will be returning a `Vec<Value>` (by virtue of the associated type). Thus, that is the type of `docs`. Our `Deserialize` implementation returns a `Documents` object, so we wrap `docs` in that.

## Full implementation

```rust
#[derive(Debug)]
struct Documents(Vec<Value>);

#[derive(Deserialize, Debug)]
struct MyData {
    documents: Documents,
    journal: Value,
}

impl<'de> Deserialize<'de> for Documents {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let visitor = DocumentVisitor;
        let docs = deserializer.deserialize_seq(visitor)?;
        Ok(Documents(docs))
    }
}

struct DocumentVisitor;

impl<'de> serde::de::Visitor<'de> for DocumentVisitor {
    type Value = Vec<Value>;

    fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(formatter, "a list")
    }

    fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
    where
        A: serde::de::SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(item) = seq.next_element()? {
            println!("Read item='{item}'");
            values.push(item)
        }
        Ok(values)
    }
}
```

## Filtering and processing
The above implementation reads and keeps every value of input. The whole idea here, though, was that we could filter/process our values, so let's now update our code to do that. We'll only keep documents that are themselves objects, then we'll take the first key-value pair (ignoring others), skipping those with null values (eg, `{ "bar": null }"`). These first key-value pairs will be aggregated into a single object returned as a vector of one object:

```rust
fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
where
    A: serde::de::SeqAccess<'de>,
{
    let mut agg_map = serde_json::Map::new();
    while let Some(item) = seq.next_element()? {
        // If `item` isn't a JSON object, we'll skip it:
        let Value::Object(map) = item else { continue };

        // Get the first element, assuming we have some
        let (k, v) = match map.into_iter().next() {
            Some(kv) => kv,
            None => continue,
        };

        // Ignore any null values; aggregate everything into a single map
        if v == Value::Null {
            continue;
        } else {
            println!("Keeping {k}={v}");
            agg_map.insert(k,v);
        }
    }

    let values = Value::Object(agg_map);
    println!("Final value is {values}");

    Ok(vec![values])
}
```

When running this code, the following output is printed to the console:

```
Keeping foo=1
Keeping baz=true
Final value is {"baz":true,"foo":1}
```