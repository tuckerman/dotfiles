#!/bin/bash
# Version 2026031701

sudo install -d -o root -g keyd -m 755 /etc/keyd

sudo tee /etc/keyd/default.conf >/dev/null << EOM
[ids]
*
-1532:02a6:797b7976

[main]
capslock = overload(capslock, esc)
leftshift = overload(leftshift, S-9)
rightshift = overload(shift, S-0)

[capslock:C]
h = left
j = down
k = up
l = right

[leftshift:S]
rightshift = overload(shift, macro(S-9 S-0))
EOM
sudo chmod 644 /etc/keyd/default.conf

sudo tee /etc/keyd/razer-huntsman-v3-pro.conf >/dev/null << EOM
[ids]
1532:02a6:797b7976

[main]
# The keyboard firmware emits leftcontrol for its Caps Lock key.
leftcontrol = overload(leftcontrol, esc)
leftshift = overload(leftshift, S-9)
rightshift = overload(shift, S-0)

[leftcontrol:C]
h = left
j = down
k = up
l = right

[leftshift:S]
rightshift = overload(shift, macro(S-9 S-0))
EOM
sudo chmod 644 /etc/keyd/razer-huntsman-v3-pro.conf

sudo systemctl restart keyd
