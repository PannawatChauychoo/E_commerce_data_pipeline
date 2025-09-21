#!/usr/bin/env bash
git ls-files | xargs -n1 dirname | cut -d/ -f1,2 | sort -u | awk -F/ '
{
  if (NF == 1) {
    top[$1] = 1
  } else {
    subdirs[$1] = subdirs[$1] $2 " "
    top[$1] = 1
  }
}
END {
  for (t in top) {
    print t
    if (t in subdirs) {
      n = split(subdirs[t], arr, " ")
      for (i=1; i<=n; i++) {
        if (arr[i] != "")
          print "│   └── " arr[i]
      }
    }
  }
}'
