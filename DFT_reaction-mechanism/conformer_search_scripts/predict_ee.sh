#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/ee_prediction.py" > ee_prediction.txt
