#!/bin/bash

function get_bounded_contexts_with_changes {
  changed_files=$(git diff --name-only HEAD)
  bounded_contexts=$(echo "$changed_files" | grep -E 'instant_python/contexts/([^/]*/)*(infra)' | sed -E 's|instant_python/contexts/([^/]*)/.*|\1|' | sort -u)
  echo "$bounded_contexts"
}

function has_bounded_contexts {
  local contexts="$1"

  if [[ -z "$contexts" ]]; then
    echo "No changes detected in infra folder of any bounded context."
    return 1
  fi

  return 0
}

function run_tests {
  local contexts="$1"

  for context in $contexts; do
    echo "Running integration tests for bounded context: $context"
    infra_folders=$(find tests/contexts/"$context" -type d -name "infra")
    {{ general.dependency_manager }} run pytest $infra_folders -ra
  done
}

function main {
  local bounded_contexts
  bounded_contexts=$(get_bounded_contexts_with_changes)

  if has_bounded_contexts "$bounded_contexts"; then
    run_tests "$bounded_contexts"
  fi
}

main