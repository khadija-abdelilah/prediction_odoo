#!/bin/bash

pip3 install --upgrade pip && pip3 install debugpy

# needed to do envsubst in entrypoint.sh
set -x; apt -y update && apt install -y gettext-base

# launch ipython from Odoo Shell
apt install -y ipython3
