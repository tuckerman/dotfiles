#!/bin/bash

KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINkglhvuFWuna9ZaP8v/I3Vy1eU1CwmqzqziBsDbO0wL"

grep -Eq "^${KEY}( |$)" "$HOME/.ssh/authorized_keys" 2>/dev/null || echo "$KEY" >> "$HOME/.ssh/authorized_keys"
