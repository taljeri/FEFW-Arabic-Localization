#!/bin/bash
# ==============================================================================
# سكربت تثبيت تعريب Fire Emblem: Fortune's Weave على محاكي Ryujinx (Mac / Linux)
# ==============================================================================
set -e

TITLE_ID="04007EF01F8AE000"

if [ "$(uname)" = "Darwin" ]; then
    RYU_MODS="$HOME/Library/Application Support/Ryujinx/mods/contents/$TITLE_ID/FEFW_Arabic_Mod"
else
    RYU_MODS="$HOME/.config/Ryujinx/mods/contents/$TITLE_ID/FEFW_Arabic_Mod"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROMFS_DIR="$SCRIPT_DIR/romfs"

echo "=========================================================="
echo "   تثبيت تعريب لعبة Fire Emblem على محاكي Ryujinx        "
echo "=========================================================="

mkdir -p "$RYU_MODS"
echo "نسخ ملفات التعريب إلى: $RYU_MODS"
cp -R "$ROMFS_DIR" "$RYU_MODS/"

echo "=========================================================="
echo "تم التثبيت بنجاح على محاكي Ryujinx! 🎉"
echo "=========================================================="
