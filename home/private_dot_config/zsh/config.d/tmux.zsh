if [ -n "$TMUX" ]; then
  session=$(echo $TMUX | cut -d, -f1 | rev | cut -d/ -f1 | rev)
  if [ -L "$HOME/.ssh/.tmux-$session-ssh-auth.sock" ]; then
    export SSH_AUTH_SOCK="$HOME/.ssh/.tmux-$session-ssh-auth.sock"
  fi
fi
