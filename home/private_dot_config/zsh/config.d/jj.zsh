if command -v jj &>/dev/null; then
  source <(jj util completion zsh)
fi

export JJ_CONFIG="${XDG_CONFIG_HOME}/jj/config.toml"
