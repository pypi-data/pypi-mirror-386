#!/bin/bash
# Helper script to run commands without old VIRTUAL_ENV interference

# Unset old VIRTUAL_ENV if it exists
unset VIRTUAL_ENV

# Run the command passed as arguments
exec "$@"
