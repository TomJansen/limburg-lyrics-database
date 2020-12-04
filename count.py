#!/usr/bin/env python3
import sys

chars = open(sys.argv[1], encoding="utf8").read().strip().replace("\n", "")
[print(c+" -", chars.count(c)) for c in sorted(set([c for c in chars]))]