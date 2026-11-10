#!/bin/bash
# ==============================================================================
# سكربت التثبيت التلقائي لتعريب Fire Emblem: Fortune's Weave على نظام الماك (nxnative)
# ==============================================================================
set -e

TITLE_ID="04007EF01F8AE000"
NXNATIVE_DIR="$HOME/Library/Application Support/nxnative/$TITLE_ID"
MOD_DIR="$NXNATIVE_DIR/arabic_mod"
ENV_FILE="$NXNATIVE_DIR/env.txt"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROMFS_DIR="$SCRIPT_DIR/romfs"

echo "=========================================================="
echo "   تثبيت تعريب لعبة Fire Emblem: Fortune's Weave (macOS)   "
echo "=========================================================="

if [ ! -d "$ROMFS_DIR" ]; then
    echo "خطأ: لم يتم العثور على مجلد romfs في: $ROMFS_DIR"
    exit 1
fi

echo "1. إنشاء المجلدات المطلوبة في مسار اللعبة..."
mkdir -p "$MOD_DIR"

echo "2. نسخ ملفات الخطوط والواجهات والنصوص المعربة..."
cp -R "$ROMFS_DIR/"* "$MOD_DIR/"

echo "3. إعداد وتفعيل المود في ملف env.txt..."
touch "$ENV_FILE"

# التأكد من عدم تكرار السطور وإضافة مسار الـ Overlay
if grep -q "DM_ROMFS_OVERLAY=" "$ENV_FILE"; then
    # استبدال السطر القديم بالمسار الصحيح
    sed -i '' "s|DM_ROMFS_OVERLAY=.*|DM_ROMFS_OVERLAY=$MOD_DIR|g" "$ENV_FILE"
else
    echo "DM_ROMFS_OVERLAY=$MOD_DIR" >> "$ENV_FILE"
fi

if ! grep -q "DM_PSO_PREPARE=" "$ENV_FILE"; then
    echo "DM_PSO_PREPARE=0" >> "$ENV_FILE"
fi

if ! grep -q "DM_FPS_TARGET=" "$ENV_FILE"; then
    echo "DM_FPS_TARGET=60" >> "$ENV_FILE"
fi

echo "=========================================================="
echo "تم التثبيت بنجاح بنسبة 100%! 🎉"
echo "المسار المثبت فيه: $MOD_DIR"
echo "يمكنك الآن تشغيل اللعبة مباشرة وستعمل باللغة العربية الفصحى."
echo "=========================================================="
