if [[ ! -o interactive ]]; then
    return
fi

compctl -K _bb bb

_bb() {
  local word words completions
  read -cA words
  word="${words[2]}"

  if [ "${#words}" -eq 2 ]; then
    completions="$(bb commands)"
  else
    completions="$(bb completions "${word}")"
  fi

  reply=("${(ps:\n:)completions}")
}
