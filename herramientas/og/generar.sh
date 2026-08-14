#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$script_dir/../.." && pwd)
html_file="$script_dir/og-domo-ia.html"
output_file="$repo_dir/assets/web/og-domo-ia.jpg"
chrome_bin="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ ! -x "$chrome_bin" ]; then
  echo "No se encontró Google Chrome en: $chrome_bin" >&2
  exit 1
fi

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/domo-og.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM
png_file="$tmp_dir/og-domo-ia.png"

"$chrome_bin" \
  --headless \
  --disable-gpu \
  --hide-scrollbars \
  --user-data-dir="$tmp_dir/chrome-profile" \
  --force-device-scale-factor=1 \
  --window-size=1200,630 \
  --virtual-time-budget=5000 \
  --default-background-color=ff1B2340 \
  --screenshot="$png_file" \
  "file://$html_file"

sips -s format jpeg -s formatOptions 85 "$png_file" --out "$output_file" >/dev/null

width=$(sips -g pixelWidth "$output_file" | awk '/pixelWidth/ { print $2 }')
height=$(sips -g pixelHeight "$output_file" | awk '/pixelHeight/ { print $2 }')
bytes=$(stat -f '%z' "$output_file")

if [ "$width" != "1200" ] || [ "$height" != "630" ]; then
  echo "Dimensiones inesperadas: ${width}x${height}" >&2
  exit 1
fi

echo "Generado: $output_file"
echo "Dimensiones: ${width}x${height}"
echo "Peso: ${bytes} bytes"
