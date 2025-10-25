#!/bin/bash

# Check linting issues with pylint.

readonly THIS_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd | xargs realpath)"
readonly ROOT_DIR="${THIS_DIR}/.."

function main() {
    if [[ $# -ne 0 ]]; then
        echo "USAGE: $0"
        exit 1
    fi

    set -e
    trap exit SIGINT

    cd "${ROOT_DIR}"

    pylint edq
    return $?
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
