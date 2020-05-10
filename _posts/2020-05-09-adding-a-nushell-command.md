---
layout: post
title:  "Adding a Nushell command"
date:   2020-05-09 10:28:25 -0700
category: code
tags: [rust]
---

I recently made [a contribution](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0) to [Nushell](https://www.nushell.sh/), adding the ability to read .eml files from the shell. I had been looking for an excuse to contribute to some Rust projects, and this proved a good place to start. It first required that I write [an .eml parser crate](https://github.com/aeshirey/EmlParser/) (which I won't go into here). With that external dependency filled, I dived into how to implement a new Nushell component. At least for my `from-eml` command, I found that I had to make the following changes (presented here in what I think is a logical order):

### Modify [`crates/nu-cli/Cargo.toml`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-4d7f442355b6c3e0ec387f5d8351e697)
* Add a reference to my crate to make it available to Nushell.

### Add [`crates/nu-cli/src/commands/from_eml.rs`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-98e7a3b8702cb1f1df8d2a9b62d46847)
* Create my command, presented as the `FromEML` struct
* Create ancillary `FromEMLArgs` struct with arguments relevant to my command. In my case, I want to be able to pass in how many bytes of the email body I want to be able to preview. This corresponds directly to the builder function [`with_body_preview` in my crate](https://github.com/aeshirey/EmlParser/blob/422551d9dcbe103a2cdf0452502a63759a91269b/src/parser.rs#L77).
* Implement `WholeStreamCommand` for my struct, conforming to the contract that hooks my built-in command into the Nu ecosystem.
* The core logic for adding my command went into a [`from_eml` function](https://github.com/nushell/nushell/blob/ad8ab5b04d2786362044fe4d66227f5ff85206f0/crates/nu-cli/src/commands/from_eml.rs#L79) -- the name isn't required to conform to the command, as it [gets called in the `WholeStreamCommand::run` impl](https://github.com/nushell/nushell/blob/ad8ab5b04d2786362044fe4d66227f5ff85206f0/crates/nu-cli/src/commands/from_eml.rs#L42).

There are a number things to understand about what's going on here, and a number of confusing points that one needs to map between the domain-specific data to Nu's data model:
* The `from-` commands -- invoked as `open filename.json --raw | from-json` (explicitly passing raw JSON data to the `from-json` command) or directly as `open filename.json` (implicitly calling `from-json`) will read in the entire file contents and pass it to you in a `RunnableContext`. You can [collect the string](https://github.com/nushell/nushell/blob/ad8ab5b04d2786362044fe4d66227f5ff85206f0/crates/nu-cli/src/commands/from_eml.rs#L87) for your own data manipulation.
* Command arguments, such as my [`FromEMLArgs`](https://github.com/nushell/nushell/blob/ad8ab5b04d2786362044fe4d66227f5ff85206f0/crates/nu-cli/src/commands/from_eml.rs#L14) appear to require Serde `Deserialize`, and if the arg contains a hyphen, you should use Serde's `rename(deserialize = "arg-name")` to change it to your field value (eg, `arg_name`).
* I believe also that the underlying Rust type is wrapped in `Tagged<T>`, though I can't explain why. This gets extracted [by accessing the `.item`](https://github.com/nushell/nushell/blob/ad8ab5b04d2786362044fe4d66227f5ff85206f0/crates/nu-cli/src/commands/from_eml.rs#L89)
* For my command, I wanted to return a dictionary of values -- an email should tell you that there's a contained `Subject` with its corresponding value; it has a `To` field that may contain one or more structured values; and so on. So I'm using the [`TaggedDictBuilder`](https://github.com/nushell/nushell/blob/cf5326443898a058683dad939daeb9c6225e7296/crates/nu-protocol/src/value/dict.rs#L198) to collect these values. This collection uses key-value pairs, but it also maintains ordering of values inserted. `TaggedDictBuilder` maps a Rust `String` to a [Nushell `Value`](https://github.com/nushell/nushell/blob/f93ff9ec33eac200da25afc57165f40752d1d936/crates/nu-protocol/src/value.rs#L32) -- be it a primitive, a row of dictionaries, etc. 
* I found the concept of tags, untagged values, and tagged values a bit wonky. A [`Tag`](https://github.com/nushell/nushell/blob/04702530a3afb3bc325bdcbf54290680d6875c17/crates/nu-source/src/meta.rs#L256) is effectively just a reference back to the command that invoked your custom command. I assume there's valid reason for threading this through various results, but for my use case, there seems no reason to keep track of this information. [Using the `TaggedDictBuilder`](https://github.com/nushell/nushell/blob/ad8ab5b04d2786362044fe4d66227f5ff85206f0/crates/nu-cli/src/commands/from_eml.rs#L47) and my structured data, I'm effectively linking the Nushell user's invocation of `from-eml` and the content of the email they're opening (eg, `To:` -> `John Smith <jsmith@example.com>`).
* It took me a while to figure out that when I parse out multiple email addresses and want to present them together, I needed to [create a `Table`](https://github.com/nushell/nushell/blob/ad8ab5b04d2786362044fe4d66227f5ff85206f0/crates/nu-cli/src/commands/from_eml.rs#L68). The resulting code is _very_ straightforward and easy to grok, but getting there took a lot of experimentation.

### Modify [`crates/nu-cli/src/cli.rs`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-d3d69b511f2537aae41e6821af841084)
* Indicate `FromEML` is a whole stream command

### Modify [`crates/nu-cli/src/commands.rs`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-85c604b2d80398f4bbd3b64bc46552ed)
* Expose the `from_eml` module and the `FromEML` struct as a usable command

### Add [`tests/fixtures/formats/sample.eml`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-21153a8e6f328c60f157ba4a4850a864)
* Sample .eml file that will be used for testing

### Modify [`crates/nu-cli/src/utils.rs`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-d686dac05472f52057cad0a2a6ee5fd2)
* Appears to add the above `sample.eml` file as a resource to build-time tests.

### Add [`crates/nu-cli/tests/format_conversions/eml.rs`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-48cd851a870eb18f6cbdde5fe0bdc72a)
* Create the tests that get run against my command. This includes actual Nushell commands to be run, testing integration of `from-eml` into Nu. For example, `open sample.eml | get To`.

### Modify [`crates/nu-cli/tests/format_conversions/mod.rs`](https://github.com/nushell/nushell/commit/ad8ab5b04d2786362044fe4d66227f5ff85206f0#diff-7dce6b8454e244726ba010592e373188)
* Expose the above `eml.rs` format conversion tests
