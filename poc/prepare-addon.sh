#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
set -eu

if [ "$#" -ne 1 ]; then
    printf 'Usage: sh %s INTERFACE_NUMBER\nExample: sh %s 120105\n' "$0" "$0" >&2
    exit 1
fi
interface=$1
case "$interface" in
    ''|*[!0-9]*) printf 'Interface number must contain only digits.\n' >&2; exit 1 ;;
esac
if [ "${#interface}" -lt 5 ] || [ "${#interface}" -gt 6 ]; then
    printf 'Interface number must be between 10000 and 999999.\n' >&2
    exit 1
fi
case "$interface" in
    0*) printf 'Interface number must not start with zero.\n' >&2; exit 1 ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
addon_dir="$script_dir/ElunesGazePoC"
template="$addon_dir/ElunesGazePoC.toc.in"
target="$addon_dir/ElunesGazePoC.toc"
if [ ! -f "$template" ]; then
    printf 'Missing template: %s\n' "$template" >&2
    exit 1
fi
if [ -e "$target" ] || [ -L "$target" ]; then
    printf 'A TOC already exists: %s\nEdit its Interface line manually to update it.\n' "$target" >&2
    exit 1
fi

# noclobber also prevents overwriting a file created after the existence check.
(set -C; sed "s/@INTERFACE@/$interface/g" "$template" > "$target")
printf 'Prepared %s for interface %s.\nCopy this folder to your Retail Interface/AddOns directory while WoW is closed.\n' "$addon_dir" "$interface"
