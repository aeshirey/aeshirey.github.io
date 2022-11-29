---
layout: post
title:  "Joinable traits"
date:   2022-11-28 07:35:54 -0700
category: code
tags: [rust]
---

I just released an update to my [`joinable` crate](https://crates.io/crates/joinable/) ([source code here](https://github.com/aeshirey/joinable)) as well as a new [`irisdata` crate](https://crates.io/crates/irisdata) ([source code](https://github.com/aeshirey/irisdata)) well-known in the data science field.

This update to `joinable` renames the `Joinable` trait to `JoinableGrouped` to reflect that the results (at least of inner- and outer-joins) group the right-hand side. It also adds a new trait with the `Joinable` name that behaves perhaps more intuitively -- each left-hand record can be yielded multiple times (as matches are found).

`Joinable` only defines `inner_join` and `outer_join` methods. `JoinableGrouped` defines `inner_join_grouped`, `outer_join_grouped`, `semi_join`, and `anti_join`.

```rust
use std::cmp::Ordering;

use irisdata::{Species, IRIS_DATA};
use joinable::{JoinableGrouped, RHS};

#[derive(Debug)]
struct IrisData {
    species: Species,
    common_name: &'static str,
    average_sepal_length: f32,
    average_sepal_width: f32,
    average_petal_length: f32,
    average_petal_width: f32,
}

fn main() {
    let common_names = [
        (Species::IrisVersicolor, "blue flag"),
        (Species::IrisVersicolor, "harlequin blueflag"),
        (Species::IrisVersicolor, "larger blue flag"),
        (Species::IrisVersicolor, "northern blue flag"),
        (Species::IrisVersicolor, "poison flag"),
        (Species::IrisVirginica, "Virginia blueflag"),
        (Species::IrisVirginica, "Virginia iris"),
        (Species::IrisVirginica, "great blue flag"),
        (Species::IrisVirginica, "southern blue flag"),
    ];

    let joined = common_names
        .iter()
        .inner_join_grouped(RHS::new_unsorted(&IRIS_DATA[..]), |(lhs_species, _), r| {
            if *lhs_species == r.species {
                Ordering::Equal
            } else {
                Ordering::Less
            }
        })
        .map(|(lhs, grp)| IrisData {
            species: lhs.0,
            common_name: lhs.1,
            average_sepal_length: grp.iter().map(|i| i.sepal_length).sum::<f32>() / grp.len() as f32,
            average_sepal_width: grp.iter().map(|i| i.sepal_width).sum::<f32>() / grp.len() as f32,
            average_petal_length: grp.iter().map(|i| i.petal_length).sum::<f32>() / grp.len() as f32,
            average_petal_width: grp.iter().map(|i| i.petal_width).sum::<f32>() / grp.len() as f32,
        })
        .collect::<Vec<_>>();

    println!("{joined:#?}");
}
```
