#!/bin/sh

# Force apt-get to run completely unattended
export DEBIAN_FRONTEND=noninteractive

# Run apt-get with quiet (-q) and assume-yes (-y) flags
apt-get update -q
apt-get install -y -q ffmpeg ssh