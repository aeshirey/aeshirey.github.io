#!/usr/bin/python3
from time import localtime
import re

KNOWN_TAGS = ['python', 'rust', 'data']

now = "%d-%02d-%02d %02d:%02d:%02d -0700" % localtime()[:6]
ymd = "%d-%02d-%02d" % localtime()[:3]

post_name = input("New post name: ").strip()

filename = ymd + '-' + re.sub('[^a-z0-9]+', '-', post_name.lower()).strip('-')
filename = "_posts/%s.md" % filename

tags = []

for known_tag in KNOWN_TAGS:
    if known_tag in post_name.lower(): tags.append(known_tag)

if len(tags) == 0:
    tags = [tag.strip() for tag in input('No tags found. Enter tags separated by a comma: ').strip().lower().split(',')]

if 'y' != input('Create post "%s"? [y/N] ' % filename).strip().lower():
    print("Cancelling")
    exit(-1)


with open(filename, 'w') as fh:
    fh.write("""---
layout: post
title:  "%s"
date:   %s
category: code
tags: [%s]
---

`TODO`
""" % (post_name, now, ', '.join(tags)))

print("Created file")
