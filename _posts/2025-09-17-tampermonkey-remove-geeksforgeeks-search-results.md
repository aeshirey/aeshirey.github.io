---
layout: post
title:  "Tampermonkey: remove GeeksForGeeks search results"
date:   2025-09-17 08:13:09 -0700
category: code
tags: [javascript]
---

I only recently installed [Tampermonkey](https://www.tampermonkey.net/) to address a relatively minor annoyance at work. Two days later, I found some spammy search results on DuckDuckGo that were bothering me, so I decided to try my hand at a Tampermonkey script to remove them. Here's the JavaScript that I wrote to remove results from DDG:

```javascript
// ==UserScript==
// @name         Delete GeeksForGeeks from DDG
// @namespace    http://tampermonkey.net/
// @version      2025-09-17
// @description  Remove GeeksForGeeks (+other!) from Duck Duck Go
// @author       Adam Shirey
// @match        http://duckduckgo.com/*
// @match        https://duckduckgo.com/*
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// ==/UserScript==

window.setTimeout(function() {
    const root = document.querySelector('ol.react-results--main');

    // Add other terms as you see fit
    const matches = [
        'geeksforgeeks'
    ];

    const articles = Array.from(root.querySelectorAll('article'));

    const matchAny = (text) => {
        if (!text) return false;
        const lower = text.toLowerCase();
        return matches.some(m => lower.includes(m.toLowerCase()));
    };

    articles.forEach(article => {
        const anchors = article.querySelectorAll('a[title]');
        for (const a of anchors) {
            if (matchAny(a.title)) {
                article.remove();
                break;
            }
        }
    });
}, 1000)
```
