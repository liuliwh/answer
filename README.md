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
Get more answers by specify -n
```shell
(dev) answer % answer python add_argument exclusive -n 2
============================================================
Answer from: https://stackoverflow.com/questions/7869345/how-to-make-python-argparse-mutually-exclusive-group-arguments-without-prefix as:
import argparse

parser = argparse.ArgumentParser()

group = parser.add_mutually_exclusive_group()
group.add_argument('-a', action='store_true')
group.add_argument('-b', action='store_true')

print parser.parse_args()

============================================================
Answer from: https://stackoverflow.com/questions/39092149/argparse-how-to-make-mutually-exclusive-arguments-optional as:
parser = argparse.ArgumentParser()
parser.add_argument('run', help='run or stop', nargs='?', choices=('run', 'stop'))
```
# TO DO
-  profile first, find the reasonable --num_answer threshhold  use poolexecutor to deal with get_answer worker.

# More Usage

```shell
(dev) answer % answer
usage: answer [-h] [-n NUM] [-v [{debug,info,warning,error,critical}]] [QUERY ...]

The code answer utility

positional arguments:
  QUERY                 the question to answer

optional arguments:
  -h, --help            show this help message and exit
  -n NUM, --num NUM     number of answers to return, shoulbe among [1,10]
  -v [{debug,info,warning,error,critical}]
                        Log level
```
