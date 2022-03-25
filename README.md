# Background
The tool is inspired by oreilly and howdoi.

**This repo is for me to practice coding, and get myself ready for interview.**

# Introduction
Get instant coding answer from the command line.
```shell
(dev) answer % answer python add_argument exclusive
import argparse

parser = argparse.ArgumentParser()

group = parser.add_mutually_exclusive_group()
group.add_argument('-a', action='store_true')
group.add_argument('-b', action='store_true')

print parser.parse_args()
```
