#!/bin/bash

# This script is used to install the pre-commit hooks.

DEST_REPO_PATH="$1"

if [ -z "$DEST_REPO_PATH" ]; then
    echo "Usage: $0 <destination repository path>"
    exit 1
fi

if [ ! -d "$DEST_REPO_PATH" ]; then
    echo "Destination repository path does not exist"
    exit 1
fi

HOOKS_PATH="$DEST_REPO_PATH/.git/hooks"
PRE_COMMIT_HOOKS_PATH="$HOOKS_PATH/pre-commit.d"
PREPARE_COMMIT_MSG_HOOKS_PATH="$HOOKS_PATH/prepare-commit-msg.d"

# TODO: add config option to specify which hooks to install
# Install pre-commit hooks
if [ ! -d "$PRE_COMMIT_HOOKS_PATH" ]; then
    mkdir -p "$PRE_COMMIT_HOOKS_PATH"
fi
cp -r hooks/pre-commit "$HOOKS_PATH/pre-commit"
cp -r hooks/pre-commit-hooks/* "$PRE_COMMIT_HOOKS_PATH/"

# Install prepare-commit-msg hooks
if [ ! -d "$PREPARE_COMMIT_MSG_HOOKS_PATH" ]; then
    mkdir -p "$PREPARE_COMMIT_MSG_HOOKS_PATH"
fi
cp -r hooks/prepare-commit-msg "$HOOKS_PATH/prepare-commit-msg"
cp -r hooks/prepare-commit-msg-hooks/* "$PREPARE_COMMIT_MSG_HOOKS_PATH/"

echo "Pre-commit hooks installed successfully"
exit 0
