#!/bin/bash

socat stdio tcp:$(/usr/local/bin/anubis $1 --ssh):22
