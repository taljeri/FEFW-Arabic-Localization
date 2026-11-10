# ⚔️ Fortune's Weave: Classical Arabic Localization & Tooling Suite (نسج القدر)

> **Complete Open-Source Fan Translation Framework, Translation Memories (TM), and LayeredFS Patch**  
> **مشروع التعريب الأدبي الكامل، وقواميس الذاكرة اللغوية، وحزمة التعديل للعبة نسج القدر**  
> **完全ファンメイド・アラビア語ローカライズフレームワーク、翻訳メモリ (TM) および LayeredFS パッチ**

---

## 📑 جدول المحتويات / Table of Contents / 目次
1. [العربية (Arabic)](#-العربية-arabic)
2. [English](#-english)
3. [日本語 (Japanese)](#-日本語-japanese)
4. [Legal & Disclaimer / إخلاء المسؤولية / 免責事項](#-legal--disclaimer)

---

## 🇸🇦 العربية (Arabic)

### 📌 نبذة عن المشروع
هذا المستودع يضم مشروع التعريب الأدبي الكامل للعبة *Fire Emblem: Fortune's Weave* (نسج القدر). تم إعداد الترجمة استناداً إلى **النص الياباني الأصلي** كمصدر وحيد للحقيقة اللغوية لضمان دقة المعاني، ومطابقة الضمائر والتذكير والتأنيث، وصياغة الحوارات بلغة فصحى أدبية راقية.

### ✨ مميزات المشروع
- **تعريب أدبي متكامل:** تغطية شاملة لكافة فصول القصة الرئيسية، وحوارات الدعم (C/B/A/S)، والمهام الجانبية، والمعسكرات، والقوائم.
- **التوافق اللغوي التام:** مراعاة دقيقة لصيغ المثنى، والجمع، والمذكر، والمؤنث بناءً على النص الياباني الأصلي.
- **معالجة النصوص البرمجية (BiDi & Reshaping):** تضمين خوارزميات التشكيل وضبط الاتجاه من اليمين إلى اليسار تلقائياً مع حماية وسوم التحكم (`<TH>`, `<BLN>`, `{c:...}`).
- **خطوط عربية مخصصة:** دمج خطوط عربية عالية الوضوح تدعم بيئة العرض بتقنية BC4 Block-Linear.

### 📂 بنية المستودع
- `tm/` — قواميس الذاكرة اللغوية (Translation Memory) بصيغة JSON مفتوحة ومفهرسة بالأرقام.
- `mod/romfs/` — ملفات التعديل الجاهزة للتركيب المباشر (Msg, Font, Layout).
- `tools/` — محركات البناء والتشكيل والتشفير الخاصة بملفات MSBT.
- `pylibs/` — مكتبات بايثون المساعدة لمعالجة النصوص.

### 🚀 طريقة التثبيت والاستخدام
1. **على نظام macOS (عبر تطبيق اللعبة):**
   - قم بنسخ محتويات مجلد `mod/romfs` إلى مسار المود في مجلد التطبيق:
     `~/Library/Application Support/nxnative/04007EF01F8AE000/arabic_mod/`
   - أو شغّل السكربت المرفق: `sh mod/install_mac.sh`.
2. **على المحاكيات (Ryujinx / Yuzu):**
   - افتح مجلد المودات للعبة (Open Mod Data Location).
   - ضع مجلد `romfs` بداخل مجلد المودات.
3. **على جهاز Nintendo Switch (Atmosphère CFW):**
   - انسخ مجلد `romfs` إلى:
     `sd:/atmosphere/contents/04007EF01F8AE000/romfs/`

---

## 🇬🇧 English

### 📌 Overview
This repository provides a complete, literary Classical Arabic localization and reverse-engineering tooling suite for *Fire Emblem: Fortune's Weave*. Built with the **original Japanese script as the definitive source of truth**, this project delivers precise grammar, dual/plural distinctions, gender agreement, and high-register literary Arabic prose.

### ✨ Key Features
- **100% Literary Localization:** Full coverage of story chapters, CBA and S-rank supports, camps, quests, items, and system menus.
- **BiDi & Tag-Safe Pipeline:** Automated right-to-left reshaping, glyph ligatures, and strict byte-level preservation of MSBT control codes (`<TH>`, `<BLN>`, `{c:...}`).
- **Custom Arabic Typography:** Native BC4 block-linear font integration designed for crisp in-game rendering.
- **Open Translation Memories:** Over 100 structured JSON translation memories for community preservation and research.

### 📂 Repository Structure
- `tm/` — Structured JSON Translation Memories indexed by line numbers.
- `mod/romfs/` — LayeredFS mod files ready for deployment (`Msg/USen`, `Font`, `Layout`).
- `tools/` — Python utilities for MSBT packing, reshaping, and pipeline verification.
- `pylibs/` — Self-contained dependencies for Arabic BiDi reshaping and compression.

### 🚀 Installation Guide
1. **macOS (Native Wrapper):**
   - Run `sh mod/install_mac.sh` or copy `mod/romfs` to `~/Library/Application Support/nxnative/04007EF01F8AE000/arabic_mod/`.
2. **Emulators (Ryujinx / Yuzu):**
   - Right-click the game title -> *Open Mod Data Location*.
   - Copy `mod/romfs` into the mod folder.
3. **Nintendo Switch (Atmosphère CFW):**
   - Copy the `romfs` directory to:
     `sd:/atmosphere/contents/04007EF01F8AE000/romfs/`

---

## 🇯🇵 日本語 (Japanese)

### 📌 プロジェクト概要
本リポジトリは、『ファイアーエムブレム フォチュンズ・ウィーヴ』向けの高品位な古典アラビア語ローカライズデータおよび翻訳ツールキットです。**日本語原文（Msg/JPja）を絶対的な正（Source of Truth）**として位置づけ、文脈に応じた話者・対象の性別（男性／女性）、双数形（デュアル）、複数形、および登場人物ごとの格式高い文体を厳密に反映しています。

### ✨ 特徴
- **完全ローカライズ:** 本編ストーリー、CBAおよびSランク支援会話、キャンプ会話、サブクエスト、UI全般を網羅。
- **制御タグ完全保護:** MSBTバイナリ内の制御タグ（`<TH>`, `<BLN>`, `{c:...}`）をバイト単位で保全しつつ、右横書き（RTL）およびアラビア文字整形を自動適用。
- **専用フォント同梱:** ゲーム内の描画エンジンに最適化されたBC4ブロックリニア形式のアラビア語フォントを実装。
- **オープンな翻訳メモリ (TM):** 行番号に紐付けられたJSON形式の翻訳メモリを完全公開。

### 🚀 インストール方法
1. **macOS (ネイティブ環境):**
   - 付属の `sh mod/install_mac.sh` を実行するか、`mod/romfs` を以下のパスへ配置してください：
     `~/Library/Application Support/nxnative/04007EF01F8AE000/arabic_mod/`
2. **エミュレータ (Ryujinx 等):**
   - ゲームタイトルを右クリックし、「Modデータ保存先を開く」を選択後、`romfs` フォルダを配置してください。
3. **Nintendo Switch 実機 (Atmosphère):**
   - SDカードの以下ディレクトリへ `romfs` を配置してください：
     `sd:/atmosphere/contents/04007EF01F8AE000/romfs/`

---

## ⚖️ Legal & Disclaimer

- **Non-Commercial Fan Project:** This project is a non-profit, volunteer fan translation intended solely for linguistic accessibility and educational purposes.
- **Trademarks & Copyrights:** *Fire Emblem* and related properties are trademarks and copyrights of **Nintendo / Intelligent Systems**.
- **Original Software Requirement:** This repository does not contain or distribute proprietary game ROMs, ISOs, or base game executables. An official copy of the original software is required to use this modification.
- **License:** The scripts, translation memories, and toolchain in this repository are released under the [MIT License](LICENSE).
