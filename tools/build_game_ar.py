#!/usr/bin/env python3
"""Assemble the Arabic localization for the WHOLE game and install it as an overlay.

Fixes over the earlier DeepSeek script:
  1. Never wipes non-Japanese strings ({c:0000...} buffers, PUA button icons \uE000..\uE2FF,
     and format strings like {c:0e01...}/{c:0e01...} dates/times/numbers stay 100% intact).
  2. Preserves runtime data variable tags ({c:0e01...}, {c:0e02...}, {c:0e07...}) and
     PUA controller button icons (\uE000..\uE2FF) inside translated Japanese lines.
  3. Calls postedit_ar.postedit() (glossary canonicalisation + spacing cleanup + speaker
     gender agreement from both Japanese line markers and character file prefixes).
"""
import json, os, re, sys, glob

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(_HERE, '..')
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(ROOT, 'pylibs'))

import backports.zstd as z
import msbt_tool as M
import romfs_patch as R
import arabic_reshaper
from bidi.algorithm import get_display
import postedit_ar as PE

DEFAULT_MAC_APP = "/Applications/Fire Emblem Fortune's Weave.app/Contents/Resources/romfs.img"
IMG = os.environ.get('FEFW_ROMFS_IMG', os.environ.get('ROMFS_PATH', DEFAULT_MAC_APP))
MOD = os.environ.get('FEFW_MOD_DIR', os.path.join(ROOT, 'mod', 'romfs'))

TAG = re.compile(r'^(?:<[A-Z]{2,4}>)+')
CTRL = re.compile(r'\{c:[0-9a-fA-F]+\}')
RUBY_CTRL = re.compile(r'\{c:0e00000000[0-9a-fA-F]*\}')
# Runtime data variable tags (numbers, unit names, dates, forge suffixes) that must not be lost:
DATA_CTRL = re.compile(r'\{c:0e0[123567][0-9a-fA-F]+\}')
PUA = re.compile(r'[\ue000-\ue2ff]')
BREAK = '{c:0a}'
BREAK2 = '{c:0a0a}'

RESHAPER = arabic_reshaper.ArabicReshaper(configuration={
    'delete_harakat': True, 'support_ligatures': True,
    'use_unshaped_instead_of_isolated': False,
})

# File-prefix default speaker gender for character-specific chapters/supports
FEMALE_FILE_PREFIXES = ('1_LED_', '1_SEO_', '1_ANH_', '1_ORH_', 'SUP_13_', 'SUP_14_')
MALE_FILE_PREFIXES   = ('1_KAI_', '1_DIT_', '1_BEL_', '1_TAL_', 'SUP_11_', 'SUP_12_')


def has_arabic(s):
    # Only shape unshaped base Arabic (U+0600..U+06FF); pre-shaped U+FE70..U+FEFC tiles are already in visual LTR order!
    return any(0x0600 <= ord(c) <= 0x06FF for c in s)


def has_jp(s):
    return any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in s)


_NORM_CHARS = str.maketrans('٠١٢٣٤٥٦٧٨٩٪〈〉《》【】', '0123456789%«»«»[]')
_FORMS_A_FIX = str.maketrans({'ﯨ': 'ﻳ', 'ﯩ': 'ﻴ', 'ﷲ': 'الله'})
_GLUED_ALEF_MAKSURA = re.compile(r'(على|إلى|حتى|متى|لدى|سوى|أخرى|شتى|كبرى|صغرى|أولى)(?=[ء-ي])')
_COLOR_SPAN_RE = re.compile(
    r'(\{c:0e000003[0-9a-fA-F]+\}(?:\{c:0e08[0-9a-fA-F]+\})?)'
    r'([^{}]*)'
    r'(\{c:(?:0e08[0-9a-fA-F]+)?0e000003000200\}\{c:ff\}\{c:00\}(?:\{c:0e08[0-9a-fA-F]+\})?)'
)


def _shape_run_rtl(seg):
    if not has_arabic(seg):
        return seg
    seg = _GLUED_ALEF_MAKSURA.sub(r'\1 ', seg)
    return get_display(RESHAPER.reshape(seg), base_dir='R').translate(_FORMS_A_FIX)


def shape(s):
    if not has_arabic(s):
        return s
    s = RUBY_CTRL.sub('', s)
    s = s.translate(_NORM_CHARS).replace('````', '').replace('``', '"').replace("''", '"')
    s = _GLUED_ALEF_MAKSURA.sub(r'\1 ', s)
    # Defensively normalize any malformed tag variants ({:0a}, {0a:}, {:0e...}) to proper {c:...}
    s = re.sub(r'\{:([0-9a-fA-F]+)\}', r'{c:\1}', s)
    s = re.sub(r'\{([0-9a-fA-F]+):\}', r'{c:\1}', s)
    s = re.sub(r'\{:c:([0-9a-fA-F]+)\}', r'{c:\1}', s)
    s = re.sub(r'\{c:([0-9a-fA-F]+):\}', r'{c:\1}', s)
    s = s.replace('{:}', '{c:0a}')
    s = s.replace('{c:0a0e', '{c:0a}{c:0e').replace('{c:000a}', '{c:00}{c:0a}')
    if BREAK2 in s:
        return BREAK2.join(shape(p) for p in s.split(BREAK2))
    return BREAK.join(shape_line(ln) for ln in s.split(BREAK))


def shape_line(line):
    if not has_arabic(line):
        return line
    line = line.replace('<>', '')
    line = _GLUED_ALEF_MAKSURA.sub(r'\1 ', line)
    prefix = ''
    m = TAG.match(line)
    if m:
        prefix, line = m.group(0), m.end() and line[m.end():]

    suffix = ''
    last_ar_idx = -1
    for i in range(len(line) - 1, -1, -1):
        if 0x0600 <= ord(line[i]) <= 0x06FF or 0xFE70 <= ord(line[i]) <= 0xFEFF:
            last_ar_idx = i
            break
    if last_ar_idx != -1:
        tail = line[last_ar_idx + 1:]
        # Only pull binary end-of-message trailers ({c:ff...}, {c:fd...}, {c:fe...}, {c:ab...}, {c:00...})
        # into suffix. NEVER pull runtime data variables ({c:0e...}) into suffix!
        m_trail = re.search(r'\{c:(?!0e)[0-9a-fA-F]+\}', tail)
        if m_trail:
            c_pos = last_ar_idx + 1 + m_trail.start()
            suffix = line[c_pos:]
            line = line[:c_pos]

    # 1. Protect paired color spans using RTL Arabic-Supplement placeholders U+0750..U+075F (BiDi class 'AL')
    #    so the colored phrase stays in its true Right-to-Left sentence position!
    spans = []
    def repl_span(mt):
        c_on, inner, c_off = mt.group(1), mt.group(2), mt.group(3)
        spans.append(c_on + _shape_run_rtl(inner) + c_off)
        return chr(0x0750 + len(spans) - 1)

    tmp = _COLOR_SPAN_RE.sub(repl_span, line)

    # 2. Protect standalone {c:...} tags and PUA icons using RTL Arabic-Supplement placeholders U+0760..U+077F (BiDi class 'AL')
    toks = []
    def keep(mt):
        toks.append(mt.group(0))
        return chr(0x0760 + len(toks) - 1)

    tmp = CTRL.sub(keep, tmp)
    tmp = PUA.sub(keep, tmp)

    # 3. Always pass base_dir='R' so lines beginning with a {c:...} tag never flip to Left-to-Right!
    out = get_display(RESHAPER.reshape(tmp), base_dir='R').translate(_FORMS_A_FIX)
    for i, t in enumerate(toks):
        out = out.replace(chr(0x0760 + i), t)
    for i, sp in enumerate(spans):
        out = out.replace(chr(0x0750 + i), sp)
    if '<BLN>' in prefix:
        out = out + '    '
    return prefix + out + suffix


def load_tm():
    tm = {}
    for p in sorted(glob.glob(os.path.join(ROOT, 'tm', '*.json'))):
        d = json.load(open(p))
        for fn, entries in d.items():
            if not fn.endswith('.msbt.zst'):
                continue
            tm.setdefault(fn, {})
            if isinstance(entries, dict):
                tm[fn].update({int(k): v for k, v in entries.items() if str(v).strip()})
            elif isinstance(entries, list):
                tm[fn].update({i: v for i, v in enumerate(entries) if str(v).strip()})
    return tm


def load_en_ar():
    p = os.path.join(ROOT, 'work', 'en_ar.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def legacy():
    sys.path.insert(0, _HERE)
    try:
        import translate_game_ar as T
        return T.EXACT_TRANSLATIONS
    except Exception:
        return {}


def _wrap_ar_line(text, max_chars=54):
    if len(text) <= max_chars or BREAK in text:
        return text
    words = text.split(' ')
    lines, cur = [], ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        lines.append(cur)
    return BREAK.join(lines)


def _try_lines(lines, cache, wrap_long=False):
    out = []
    for ln in lines:
        plain = CTRL.sub('', ln)
        plain = PUA.sub('', plain).strip()
        if not plain:
            keep_only = ''.join(DATA_CTRL.findall(ln) + PUA.findall(ln))
            out.append(keep_only)
            continue
        if not has_jp(plain):
            out.append(ln)
            continue
        got = cache.get(plain)
        if got is None:
            # Also try without ruby/furigana or ideographic spaces if any
            got = cache.get(plain.replace('\u3000', ' ').strip())
        if got is None:
            return None
        data_tags = DATA_CTRL.findall(ln)
        pua_icons = PUA.findall(ln)
        extra_tokens = [t for t in (data_tags + pua_icons) if t not in got]
        if extra_tokens:
            if '""' in got:
                got = got.replace('""', '«' + extra_tokens[0] + '»', 1)
                extra_tokens = extra_tokens[1:]
            if extra_tokens:
                # In Arabic (VSO/RTL), runtime variables that were not explicitly placed inside
                # the sentence belong after the Arabic phrase, separated by spaces so tags never glue.
                got = got + ' ' + ' '.join(extra_tokens)
        if wrap_long:
            got = _wrap_ar_line(got)
        out.append(got)
    return out


def ar_from_japanese(jp_string, cache):
    """Japanese MSBT string -> Arabic string, preserving data tags and PUA icons."""
    if not has_jp(jp_string):
        return None
    prefix = ''
    m = TAG.match(jp_string)
    if m:
        prefix, body = m.group(0), jp_string[m.end():]
    else:
        body = jp_string
    # 1. Try splitting with compound {c:0a0e...} normalized into {c:0a}{c:0e...}
    b1 = body.replace('{c:0a0e', '{c:0a}{c:0e').replace('{c:000a}', '{c:00}{c:0a}').replace(BREAK2, BREAK)
    out = _try_lines(b1.split(BREAK), cache, wrap_long=False)
    if out is None:
        # 2. Fallback: mt_cache stored strings with {c:0a0e...} unsplit; look up unsplit and word-wrap!
        b2 = body.replace(BREAK2, BREAK)
        out = _try_lines(b2.split(BREAK), cache, wrap_long=True)
    if out is None:
        return None
    return prefix + BREAK.join(out)


def detect_gender(fn, jp_str):
    g = PE.speaker_gender(jp_str)
    if g in ('f', 'm'):
        return g
    # Also check feminine sentence-ending particles in Japanese
    if re.search(r'(?:わよ|わね|かしら|なのよ|だわ|ますわ)[。！？…」]*$', jp_str.strip()):
        return 'f'
    if re.search(r'(?:だぜ|だぞ|るぜ|るぞ|ようぜ)[。！？…」]*$', jp_str.strip()):
        return 'm'
    if fn.startswith(FEMALE_FILE_PREFIXES):
        return 'f'
    if fn.startswith(MALE_FILE_PREFIXES):
        return 'm'
    return g


def main():
    install = '--install' in sys.argv
    jp = json.load(open(os.path.join(ROOT, 'work', 'jpja_all.json')))
    cache = {}
    for cp in sorted(glob.glob(os.path.join(ROOT, 'work', 'mt_cache*.json'))):
        cache.update(json.load(open(cp)))
    tm = load_tm()
    leg = legacy()
    en_ar = load_en_ar()

    idx = R.read_index(IMG)
    files = sorted(k for k in idx if k.startswith('Msg/USen/') and k.endswith('.msbt.zst'))
    file_filter = None
    for arg in sys.argv:
        if arg.startswith('--filter='):
            file_filter = arg.split('=', 1)[1]
    if file_filter:
        files = [k for k in files if file_filter in k]
    os.makedirs(os.path.join(MOD, 'Msg', 'USen'), exist_ok=True)

    tot = cov = 0
    miss = 0
    with open(IMG, 'rb') as f:
        for k in files:
            fn = k.split('/')[-1]
            d, off, size = idx[k]
            f.seek(off)
            raw = z.decompress(f.read(size))
            to, ts = M.txt2_of(raw)
            raw_strs = M.read_txt2(raw, to, ts)
            usen = [M.decode(s) for s in raw_strs]
            jps = jp.get(fn, [])

            out, n, c = [], len(usen), 0
            for i, s in enumerate(usen):
                # 1. Authoritative index-keyed TM (tm/*.json)
                ar = tm.get(fn, {}).get(i)
                # 2. Hand-authored dictionary (EXACT_TRANSLATIONS)
                if ar is None and s in leg:
                    ar = leg[s]
                # 3. Japanese -> Arabic MT with glossary + speaker-gender agreement + tag preservation
                if ar is None and i < len(jps) and jps[i].strip():
                    ar = ar_from_japanese(jps[i], cache)
                    if ar is not None:
                        g = detect_gender(fn, jps[i])
                        ar = PE.postedit(ar)
                        ar = PE.agree_with_speaker(ar, g)
                # 4. English -> Arabic fallback for strings that had no Japanese in Msg/JPja/
                if ar is None and s in en_ar:
                    ar = PE.postedit(en_ar[s])

                if ar is not None:
                    out.append(M.encode(shape(ar)))
                    c += 1
                else:
                    out.append(raw_strs[i])
            tot += n
            cov += c
            rebuilt_comp = z.compress(M.rebuild(raw, out), level=19)
            dist_path = os.path.join(ROOT, 'mod', 'romfs', 'Msg', 'USen')
            os.makedirs(dist_path, exist_ok=True)
            open(os.path.join(dist_path, fn), 'wb').write(rebuilt_comp)
            if install and MOD != os.path.join(ROOT, 'mod', 'romfs'):
                mod_out = os.path.join(MOD, 'Msg', 'USen')
                os.makedirs(mod_out, exist_ok=True)
                open(os.path.join(mod_out, fn), 'wb').write(rebuilt_comp)

    print(f"files {len(files)}  total_strings {tot:,}  translated_arabic {cov:,}  preserved_control_or_blank {tot - cov:,}")


if __name__ == '__main__':
    main()
