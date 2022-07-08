---
layout: post
title:  "SMT for scheduling scouts in tents"
date:   2022-07-07 22:43:17 -0700
category: code
tags: [smt]
---

Yesterday, the adults of my kids' scout troop had a video call to discuss the upcoming week-long camp many of the scouts will attend. One of the mundane tasks is to figure out which scouts will bunk with which other scouts. There are maybe 20 or so scouts of different ages, genders, and personalities, and they need to be placed into a limited number of tents or cabins.

I wasn't personally involved in the phone call, but I was call-adjacent and aghast at the pen-and-paer approach to figuring out who should be where. Parents expressed their interest in having their kids _with_ this scout but _not with_ that scout. Boys and girls can't share a tent. Scouts may only share a tent with other scouts within three years of age (ie, no 17 year-old scouts bunking with 12 year-olds). The mental effort and time that went into that work annoyed my inner geek, so I proceeded to spend the next several hours solving the general case. It was a good excuse to play around with SMT again.

Rather than dive into all the details, I'll simply share [the public Gist with my v1 implementation](https://gist.github.com/aeshirey/0d8f4d2081217ded2ca6f5888e1f894f).

The solution is a Python script that generates SMT-LIB code that is evaluated by [Z3](). After a few configurations (such as `NUM_TENTS` to identify how many tents are available), you specify the set of scouts with their age and gender:

```python
scouts = [
        ('Abe', 14, 'm'),     # 0
        ('Brian', 13, 'm'),   # 1
        ('Charlie', 14, 'm'), # 2
        ('Dave', 13, 'm'),    # 3
        ('Eddie', 14, 'm'),   # 4
        ('Lily', 15, 'f'),    # 5
        ('Megan', 14, 'f'),   # 6
        ]
```

The output is a model that tells you who is in which tent. In this example, tent0 contains scouts 5 (Lily) and 6 (Megan):

```
  (define-fun tent0 ((x!0 Int)) Int
    (ite (= x!0 2) 5
    (ite (= x!0 3) 6
      (- 1))))
```
