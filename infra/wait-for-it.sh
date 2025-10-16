#!/bin/bash
# wait-for-it.sh: Wait for a service to be ready
# Usage: ./wait-for-it.sh host:port [command]
#
# Example:
#   ./wait-for-it.sh localhost:5432
#   ./wait-for-it.sh localhost:5432 -- echo "Database is ready"

set -e

TIMEOUT=30
QUIET=0
cmd=""
while [[ $# -gt 0 ]]; do
    case $1 in
        *:*)
            host_port="$1"
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --quiet)
            QUIET=1
            shift
            ;;
        --)
            shift
            cmd="$@"
            break
            ;;
        *)
            shift
            ;;
    esac
done

if [[ -z "$host_port" ]]; then
    echo "Usage: $0 host:port [--timeout TIMEOUT] [--quiet] [-- command]"
    exit 1
fi

host="${host_port%:*}"
port="${host_port#*:}"

echo "Waiting for $host:$port (timeout: ${TIMEOUT}s)..."

elapsed=0
while ! (echo >/dev/tcp/$host/$port 2>/dev/null || nc -z $host $port 2>/dev/null); do
    if [[ $elapsed -ge $TIMEOUT ]]; then
        echo "Timeout: Service $host:$port did not become ready after ${TIMEOUT}s"
        exit 1
    fi
    elapsed=$((elapsed + 1))
    sleep 1
done

echo "Service $host:$port is ready!"

if [[ -n "$cmd" ]]; then
    exec $cmd
fi
