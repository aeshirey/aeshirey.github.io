---
layout: post
title:  "Comparing Regex performance in Rust and C#"
date:   2021-03-01 22:31:34 -0700
category: code
tags: [rust, c#]
---

I ran a test at work the other day comparing different ways to try to optimize [regular expressions in C#](https://docs.microsoft.com/en-us/dotnet/api/system.text.regularexpressions.regex?view=net-5.0). Then I wondered how that compares with Rust. My use case was a series of some pretty gnarly regexes with backtracing, backreferences, and multiple named groupings. I ran ten or so of them sequentially on each input which might be in the 10-100 KiB range, and in total, I had maybe tens or hundreds of thousands of such inputs. So we're not talking about saving a few milliseconds - potential performance gains here would be nontrivial.

Rather than running the same test for work, I wanted to simulate _something_ that I could post publicly - even if it's not the same thing. So I started by grabbing the first partial file of the [February 20 FR Wikimedia dump](https://dumps.wikimedia.org/frwiki/20210220/), which is 2.1 GiB decompressed, 22.6M lines of XML.

Then, completely arbitrarily, I wrote some regular expressions to detect the `<contributor>` opening tag, which seems to be followed always by either a `<username>` or an `<ip>`, an the IP is either v4 or v6.

```xml
      <timestamp>2021-01-14T22:26:27Z</timestamp>
      <contributor>
        <username>Freddo</username>
        <id>72266</id>
      </contributor>
      <minor />
      <comment>/* Fêtes et jours fériés */</comment>
```

My simple test runs one regex to find the contributor tag, one to check for IP, and on an IP match, runs one to check for IPv4 or another for IPv6; on an IP mismatch, it runs one last regex to check for the username. It's not what you'd run in "real" code, but it's an okay proxy.

The Rust code, using [`regex = "1.4.3"`](https://crates.io/crates/regex), is:

```rust
use regex::Regex;
use std::{
    fs,
    io::{BufRead, BufReader, Read},
};

fn main() {
    let contributor_re = Regex::new("<contributor>").unwrap();
    let username_re = Regex::new("<username>([^<]+)</username>").unwrap();
    let ip_re = Regex::new("<ip>([^<]+)</ip>").unwrap();
    let ipv4_re = Regex::new(r#"^\d+\.\d+\.\d+\.\d+$"#).unwrap();
    let ipv6_re = Regex::new("^[0-9A-F:]+").unwrap();

    let filename = "../frwiki-20210220-pages-articles-multistream1.xml-p1p306134";
    let fh = fs::File::open(filename).unwrap();
    let buf = BufReader::new(fh);

    let mut prev_contributor = false;
    let mut usernames = 0;
    let mut ipv4s = 0;
    let mut ipv6s = 0;

    for line in buf.lines() {
        let line = line.unwrap();
        if prev_contributor {
            if let Some(cap) = ip_re.captures(&line) {
                let ip = cap.get(1).unwrap().as_str();
                // is it ipv4 or ipv6?
                if let Some(capv4) = ipv4_re.captures(ip) {
                    ipv4s += 1;
                } else if let Some(capv6) = ipv6_re.captures(ip) {
                    ipv6s += 1;
                }
            } else if username_re.is_match(&line) {
                usernames += 1;
            }
            prev_contributor = false;
        } else {
            prev_contributor = contributor_re.is_match(&line);
        }
    }

    println!(
        "Found {} usernames, {} IPv4 addresses, {} IPv6 addresses",
        usernames, ipv4s, ipv6s
    );
}
```

When I ran this on a release build, I got my counts and baseline performance time:


```bash
$ time ./target/release/regex-rust
Found 154395 usernames, 8162 IPv4 addresses, 3884 IPv6 addresses

real    0m7.737s
user    0m7.163s
sys     0m0.497s
```

Next, I translated this to C# -- specifically, a .NET Core 5 executable running on the same machine:

```csharp
using System;
using System.IO;
using System.Text.RegularExpressions;

namespace ParseWikipedia
{
    class Program
    {
        static void Main(string[] args)
        {
            Regex contributor_re = new Regex("<contributor>"),
                 username_re = new Regex("<username>([^<]+)</username>"),
                 ip_re = new Regex("<ip>([^<]+)</ip>"),
                 ipv4_re = new Regex(@"^\d+\.\d+\.\d+\.\d+$"),
                 ipv6_re = new Regex("^[0-9A-F:]+");

            string filename = "../frwiki-20210220-pages-articles-multistream1.xml-p1p306134";

            bool prev_contributor = false;
            int usernames = 0,
                ipv4s = 0,
                ipv6s = 0;
            using (StreamReader sr = new StreamReader(filename))
            {
                while (!sr.EndOfStream)
                {
                    string line = sr.ReadLine();
                    if (prev_contributor)
                    {
                        Match m = ip_re.Match(line);
                        if (m.Success)
                        {
                            string ip = m.Groups[1].Value;

                            // is it ipv4 or ipv6?
                            m = ipv4_re.Match(ip);
                            if (m.Success)
                            {
                                ipv4s += 1;
                            }
                            else
                            {
                                m = ipv6_re.Match(ip);
                                if (m.Success)
                                {
                                    ipv6s += 1;
                                }
                            }
                        }
                        else if (username_re.IsMatch(line))
                        {
                            usernames += 1;
                        }
                        prev_contributor = false;
                    }
                    else
                    {
                        prev_contributor = contributor_re.IsMatch(line);
                    }
                }
            }

            Console.WriteLine($"Found {usernames} usernames, {ipv4s} IPv4 addresses, {ipv6s} IPv6 addresses");
        }
    }
}
```

Note that I'm mixing and matching use of `Regex.Match` and `Regex.IsMatch` to be artificially _inefficient_. But I'm doing the same thing in Rust and in C#. The C# code was slower:

```bash
$ time ./bin/Release/net5.0/regex-csharp
Found 154395 usernames, 8162 IPv4 addresses, 3884 IPv6 addresses

real    0m14.621s
user    0m13.552s
sys     0m0.945s
```

The C# code was nearly half the speed as Rust. This covers both the stream reading _and_ the regular expressions, so I also tested both programs that just churn through the data counting lines: Rust's `user` time was 5.094s versus C#'s 9.335s.

One last test was to add `lto = "fat"` and `codegen-units = 1` to the Cargo.toml. This sped up Rust by about 15%:

```bash
$ time ./target/release/regex-rust
Found 154395 usernames, 8162 IPv4 addresses, 3884 IPv6 addresses

real    0m6.552s
user    0m6.092s
sys     0m0.460s
```

While not quite a scientifically rigorous test, I'm still impressed with the ease with which this simple test can be sped up by 2x.
