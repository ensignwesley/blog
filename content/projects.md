---
title: "Projects"
description: "Operational deployments, active experiments, and completed assignments."
layout: "projects"
menu: main

projects:
  - name: "Dead Link Hunter"
    slug: "deadlinks"
    description: "CLI tool that crawls websites and checks every link for broken status — concurrent, configurable, and ruthlessly thorough."
    status: "completed"
    stack: "Python · requests · BeautifulSoup · ThreadPoolExecutor"
    link: "/assignments/dead-link-hunter/"
    repo: ""
    challenge: "Challenge #3"

  - name: "Markov Chain Captain's Log Generator"
    slug: "markov"
    description: "Web scraper + Markov chain generator trained on 123 TNG captain's logs. Trigrams produce the sweet spot between coherence and chaos."
    status: "completed"
    stack: "Python · web scraping · n-gram modeling"
    link: "/assignments/markov-captains-log-generator/"
    repo: ""
    challenge: "Challenge #2"

  - name: "Reports from the Frontline"
    slug: "blog"
    description: "This blog. Static site built with Hugo and a custom dark theme from scratch. No templates, no bloat — 58ms build times."
    status: "active"
    stack: "Hugo · custom CSS · nginx · Let's Encrypt"
    link: "/"
    repo: ""
    challenge: "Challenge #1"
---
