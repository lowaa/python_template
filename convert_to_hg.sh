#!/bin/bash

# Exit on any non zero return code
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd $DIR

# Make sure we clean up
function finish {
    echo 'Script exiting...'
    # Return to the original directory
    popd
}
trap finish EXIT

hg init
hg add .
hg commit -m 'initial commit'

exit 0
