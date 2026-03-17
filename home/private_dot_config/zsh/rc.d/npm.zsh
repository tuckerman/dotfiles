if [ -d "$XDG_DATA_HOME/npm/bin" ]; then
  export PATH="$XDG_DATA_HOME/npm/bin:$PATH"
fi

if [ -d "$HOME/.npm-global/bin" ]; then
  export PATH="$HOME/.npm-global/bin:$PATH"
fi
