if command -v gls &> /dev/null; then
  alias ls='gls --hyperlink'
fi

if command -v ggrep &> /dev/null; then
  alias grep='ggrep'
fi

if command -v gmake &> /dev/null; then
  alias make='gmake'
fi
