if [ -d /opt/homebrew/share/zsh/site-functions ]; then
  FPATH="/opt/homebrew/share/zsh/site-functions:$FPATH"
fi

if command -v terraform &>/dev/null; then
  if [ -f /opt/homebrew/bin/terraform ]; then
    complete -o nospace -C /opt/homebrew/bin/terraform terraform
  fi
fi

if [ -d /opt/homebrew/Caskroom/google-cloud-sdk ]; then
  source /opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/completion.bash.inc
fi

if [ -f /opt/homebrew/etc/bash_completion.d/az ]; then
  source /opt/homebrew/etc/bash_completion.d/az
fi