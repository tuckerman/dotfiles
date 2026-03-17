#!/bin/bash
# Version 2026031701

if [ ! -d /etc/keyd ]; then
  sudo mkdir -p /etc/keyd
  sudo chown root:keyd /etc/keyd
  sudo 644 /etc/keyd
fi

if [ !  -s /etc/keyd/default.conf ]; then
  sudo tee /etc/keyd/default.conf << EOM
[ids]
*

[main]
capslock = overload(capslock, esc)
leftshift = timeout(overload(leftshift, S-9), 500, layer(leftshift))
rightshift = timeout(overload(shift, S-0), 500, layer(shift))

[capslock:C]
h = left
j = down
k = up
l = right

[leftshift:S]
rightshift = overload(shift, macro(S-9 S-0))
EOM
fi

sudo systemctl restart keyd
