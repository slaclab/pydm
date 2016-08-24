#!/bin/bash
cd `dirname -- $(readlink -f $0)`
source ../pydm_env.sh
python -m unittest discover -v
