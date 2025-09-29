alias ll='ls -lsah'

if command -v bazel &> /dev/null; then
  alias blaze='bazel'
fi

if command -v wget &> /dev/null; then
  alias wget='wget --no-hsts'
fi
