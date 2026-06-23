#!/usr/bin/env python3
"""
build.py — native_crm_v2.md → native_crm_v2.html 빌드 스크립트
사용법:  python3 build.py
         python3 build.py --input my_slides.md --output my_slides.html
         python3 build.py --watch   # MD 파일 변경 시 자동 재빌드
"""

import re, sys, os, argparse, time

# ─────────────────────────────────────────
# MD 파싱 유틸
# ─────────────────────────────────────────

def escape_html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def md_inline(text):
    """인라인 마크다운(볼드, 코드, 이탤릭) → HTML"""
    # `` code ``
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # *italic*
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text

def md_table_to_html(lines):
    """마크다운 테이블 라인 리스트 → HTML table"""
    rows = [l.strip().strip('|').split('|') for l in lines if l.strip() and not re.match(r'^\s*\|?\s*[-:]+', l)]
    if not rows:
        return ''
    html = ['<table class="tbl">']
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row]
        tag = 'th' if i == 0 else 'td'
        html.append('  <tr>')
        for c in cells:
            align = ''
            if c.startswith(':') or len(c) > 30:
                align = ' class="left"'
            html.append(f'    <{tag}{align}>{md_inline(c)}</{tag}>')
        html.append('  </tr>')
    html.append('</table>')
    return '\n'.join(html)

def md_list_to_html(items):
    """불릿 항목 리스트 → HTML ul"""
    html = ['<ul style="font-size:13px;line-height:2;padding-left:18px">']
    for item in items:
        html.append(f'  <li>{md_inline(item)}</li>')
    html.append('</ul>')
    return '\n'.join(html)

def blockquote_to_html(text):
    return f'<div class="insight">{md_inline(text)}</div>'

def parse_section_body(lines):
    """### 이하 본문 라인들 → HTML 블록 리스트"""
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # #### 소제목
        if line.startswith('#### '):
            blocks.append(f'<h4 style="font-size:13px;font-weight:700;color:#FEE500;margin:12px 0 6px">{md_inline(line[5:])}</h4>')
            i += 1
            continue

        # > blockquote
        if line.startswith('> '):
            text = line[2:]
            # 연속된 blockquote 합치기
            while i + 1 < len(lines) and lines[i+1].startswith('> '):
                i += 1
                text += ' ' + lines[i][2:]
            blocks.append(blockquote_to_html(text))
            i += 1
            continue

        # 테이블
        if line.startswith('|'):
            tbl_lines = []
            while i < len(lines) and lines[i].startswith('|'):
                tbl_lines.append(lines[i])
                i += 1
            blocks.append(md_table_to_html(tbl_lines))
            continue

        # 불릿 리스트
        if line.startswith('- '):
            items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append(lines[i][2:])
                i += 1
            blocks.append(md_list_to_html(items))
            continue

        # 빈 줄
        if line.strip() == '':
            i += 1
            continue

        # 일반 텍스트
        para = line
        while i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith(('#', '>', '|', '-', '`')):
            i += 1
            para += '\n' + lines[i]
        blocks.append(f'<p style="font-size:13px;line-height:1.8;color:#F0F0F0">{md_inline(para.replace(chr(10), "<br>"))}</p>')
        i += 1

    return '\n'.join(b for b in blocks if b)


def parse_slide(title, body_lines):
    """슬라이드 1개의 body_lines → HTML 슬라이드 div 내부"""
    # ### 로 섹션 분리
    sections = []
    current_section = None
    current_lines = []

    for line in body_lines:
        if line.startswith('### '):
            if current_section is not None:
                sections.append((current_section, current_lines))
            current_section = line[4:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section is not None:
        sections.append((current_section, current_lines))
    elif current_lines:
        sections.append((None, current_lines))

    html_parts = []

    # 섹션 없이 바로 본문인 경우 (커버 등)
    if not sections:
        return ''

    for sec_title, sec_lines in sections:
        sec_html = parse_section_body(sec_lines)
        if not sec_html.strip():
            continue

        if sec_title:
            card = f'''<div class="card" style="margin-bottom:14px">
  <div class="card-title">{escape_html(sec_title)}</div>
  {sec_html}
</div>'''
        else:
            card = f'<div style="margin-bottom:14px">{sec_html}</div>'

        html_parts.append(card)

    return '\n'.join(html_parts)


def md_to_slides(md_text):
    """MD 전체 → 슬라이드 데이터 리스트 [(num, title, body_html)]"""
    lines = md_text.splitlines()
    slides = []
    current_num = None
    current_title = ''
    current_body = []

    for line in lines:
        m = re.match(r'^## Slide (\w+) — (.+)$', line)
        if m:
            if current_num is not None:
                slides.append((current_num, current_title, current_body[:]))
            current_num = m.group(1)
            current_title = m.group(2).strip()
            current_body = []
        elif line.strip() == '---' and current_num is not None:
            continue  # 구분선 무시
        elif current_num is not None:
            current_body.append(line)

    if current_num is not None:
        slides.append((current_num, current_title, current_body[:]))

    return slides


# ─────────────────────────────────────────
# HTML 빌드
# ─────────────────────────────────────────

DARK_CSS = '''
  :root {
    --yellow: #FEE500;
    --yellow-dk: #E6CE00;
    --bg: #1A1A1A;
    --card: #242424;
    --text: #F0F0F0;
    --sub: #888;
    --border: #333;
    --accent: #FF7A50;
    --blue: #5B9BF8;
    --green: #3ECF6C;
    --purple: #A78BFA;
    --orange: #FFA940;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    background: #0A0A0A;
    color: #F0F0F0;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    padding: 20px;
  }
  .deck { width: 960px; }
  .slide { display: none; background: var(--bg); border-radius: 16px; overflow: hidden; min-height: 580px; border: 1px solid #2a2a2a; }
  .slide.active { display: block; }
  .slide-header { background: #0D0D0D; padding: 20px 36px 16px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #2a2a2a; }
  .slide-header .tag { background: var(--yellow); color: #111; font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
  .slide-header h2 { color: #F0F0F0; font-size: 17px; font-weight: 700; line-height: 1.3; }
  .slide-body { padding: 28px 36px 36px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 18px 22px; }
  .card-title { font-size: 10px; font-weight: 700; color: #666; letter-spacing: .06em; text-transform: uppercase; margin-bottom: 12px; }
  .tbl { width: 100%; border-collapse: collapse; font-size: 12px; }
  .tbl th { background: #1E1E1E; font-weight: 700; padding: 8px 10px; border: 1px solid #333; text-align: center; color: #aaa; white-space: nowrap; }
  .tbl td { padding: 7px 10px; border: 1px solid #2a2a2a; text-align: center; color: #F0F0F0; }
  .tbl td.left { text-align: left; }
  .tbl tr:hover td { background: #2a2a2a; }
  .insight { background: #1E1A00; border-left: 4px solid var(--yellow); padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; line-height: 1.7; color: #E0D080; margin: 10px 0; }
  strong { color: #FFA940; }
  code { background: #2a2a2a; color: #FEE500; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
  .nav { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; }
  .nav button { background: #1E1E1E; color: #F0F0F0; border: 1px solid #333; padding: 9px 22px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; transition: background .15s; }
  .nav button:hover { background: #2a2a2a; }
  .nav button:disabled { opacity: .3; cursor: default; }
  .nav .page-info { color: #555; font-size: 13px; }
  .progress-bar { height: 3px; background: #1E1E1E; border-radius: 2px; margin-bottom: 10px; }
  .progress-fill { height: 100%; background: var(--yellow); border-radius: 2px; transition: width .3s; }
  /* COVER */
  .cover-wrap { background: #000; min-height: 580px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 56px 40px; position: relative; overflow: hidden; }
  .cover-wrap::before { content: ''; position: absolute; width: 500px; height: 500px; background: radial-gradient(circle, rgba(254,229,0,.14) 0%, transparent 70%); top: -100px; right: -100px; }
  .cover-wrap::after { content: ''; position: absolute; width: 400px; height: 400px; background: radial-gradient(circle, rgba(254,229,0,.07) 0%, transparent 70%); bottom: -80px; left: -80px; }
  .cover-title { font-size: 34px; font-weight: 900; color: #fff; line-height: 1.25; margin-bottom: 10px; position: relative; z-index: 1; }
  .cover-title span { color: var(--yellow); }
  .cover-sub { font-size: 15px; color: rgba(255,255,255,.5); margin-bottom: 44px; line-height: 1.7; position: relative; z-index: 1; }
  .cover-badge { background: var(--yellow); color: #111; font-size: 11px; font-weight: 800; padding: 4px 14px; border-radius: 20px; margin-bottom: 22px; display: inline-block; position: relative; z-index: 1; }
  .cover-stats { display: flex; gap: 36px; position: relative; z-index: 1; }
  .cover-stat .n { font-size: 30px; font-weight: 900; color: var(--yellow); }
  .cover-stat .l { font-size: 11px; color: rgba(255,255,255,.4); margin-top: 5px; line-height: 1.4; }
  .cover-divider { width: 1px; background: rgba(255,255,255,.1); align-self: stretch; }
  .cover-date { position: absolute; bottom: 22px; right: 28px; font-size: 11px; color: rgba(255,255,255,.2); z-index: 1; }
'''

NAV_JS = '''
  const slides = Array.from(document.querySelectorAll('.slide'));
  let current = 0;
  function show(idx) {
    slides[current].classList.remove('active');
    current = idx;
    slides[current].classList.add('active');
    document.getElementById('prevBtn').disabled = current === 0;
    document.getElementById('nextBtn').disabled = current === slides.length - 1;
    document.getElementById('pageInfo').textContent = (current + 1) + ' / ' + slides.length;
    document.getElementById('progressFill').style.width = ((current + 1) / slides.length * 100) + '%';
  }
  function moveTo(dir) {
    const n = current + dir;
    if (n >= 0 && n < slides.length) show(n);
  }
  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') moveTo(1);
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   moveTo(-1);
  });
  document.getElementById('pageInfo').textContent = '1 / ' + slides.length;
  document.getElementById('progressFill').style.width = (1 / slides.length * 100) + '%';
'''


def render_cover(num, title, body_lines):
    """커버 슬라이드 전용 렌더러"""
    # 테이블에서 수치 추출
    stats = []
    for line in body_lines:
        m = re.match(r'\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|', line)
        if m:
            stats.append((m.group(1).strip(), m.group(2).strip()))

    stats_html = ''
    if stats:
        items = []
        for val, label in stats:
            items.append(f'<div class="cover-stat"><div class="n">{val}</div><div class="l">{label.replace(chr(10), "<br>")}</div></div>')
        stats_html = '<div class="cover-divider"></div>'.join(items)
        stats_html = f'<div class="cover-stats">{stats_html}</div>'

    # 부제목 (첫 번째 문단)
    subtitle_lines = []
    for line in body_lines:
        if line.strip() and not line.startswith('|') and not line.startswith('#'):
            subtitle_lines.append(line.strip())
        if len(subtitle_lines) == 2:
            break
    subtitle = '<br>'.join(subtitle_lines) if subtitle_lines else ''

    return f'''<div class="slide active" id="slide-{num}">
  <div class="cover-wrap">
    <span class="cover-badge">KAKAO CHANNEL · NATIVE CRM 2.0</span>
    <h1 class="cover-title">카카오 채널의 <span>모든 접점</span>을<br>CRM 트리거로</h1>
    <p class="cover-sub">{subtitle}</p>
    {stats_html}
    <div class="cover-date">2026.06 | 카카오 비즈니스</div>
  </div>
</div>'''


def build_html(md_path, out_path):
    with open(md_path, encoding='utf-8') as f:
        md_text = f.read()

    # 제목 추출
    doc_title = '# ' + re.search(r'^# (.+)', md_text, re.M).group(1) if re.search(r'^# (.+)', md_text, re.M) else 'Native CRM 2.0'

    slides_data = md_to_slides(md_text)
    slide_htmls = []

    for idx, (num, title, body_lines) in enumerate(slides_data):
        is_cover = (idx == 0)

        if is_cover:
            slide_htmls.append(render_cover(num, title, body_lines))
            continue

        # 일반 슬라이드
        body_html = parse_slide(title, body_lines)

        slide_id = f'slide-{num}'
        active = ''
        html = f'''<div class="slide{active}" id="{slide_id}">
  <div class="slide-header">
    <span class="tag">SLIDE {num}</span>
    <h2>{escape_html(title)}</h2>
  </div>
  <div class="slide-body">
{body_html}
  </div>
</div>'''
        slide_htmls.append(html)

    slides_joined = '\n\n'.join(slide_htmls)

    html_out = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Native CRM 2.0 — 카카오 채널의 모든 접점을 CRM 트리거로</title>
<style>
{DARK_CSS}
</style>
</head>
<body>
<div class="deck">

  <div class="progress-bar">
    <div class="progress-fill" id="progressFill" style="width:4%"></div>
  </div>

{slides_joined}

  <div class="nav">
    <button id="prevBtn" onclick="moveTo(-1)" disabled>← 이전</button>
    <span class="page-info" id="pageInfo">1 / {len(slides_data)}</span>
    <button id="nextBtn" onclick="moveTo(1)">다음 →</button>
  </div>

</div>
<script>
{NAV_JS}
</script>
</body>
</html>'''

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_out)

    print(f'✓ 빌드 완료: {out_path}  ({len(slides_data)}장)')
    return True


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='MD 슬라이드 파일을 카카오 다크테마 HTML로 빌드합니다.'
    )
    parser.add_argument('--input',  '-i', default='native_crm_v2.md',
                        help='입력 MD 파일 (기본값: native_crm_v2.md)')
    parser.add_argument('--output', '-o', default='native_crm_build.html',
                        help='출력 HTML 파일 (기본값: native_crm_build.html)')
    parser.add_argument('--watch',  '-w', action='store_true',
                        help='MD 파일 변경 감지 시 자동 재빌드')
    args = parser.parse_args()

    md_path  = args.input
    out_path = args.output

    if not os.path.exists(md_path):
        print(f'❌ 파일 없음: {md_path}')
        sys.exit(1)

    build_html(md_path, out_path)

    if args.watch:
        print(f'👀 감시 중: {md_path}  (Ctrl+C로 종료)')
        last_mtime = os.path.getmtime(md_path)
        try:
            while True:
                time.sleep(1)
                mtime = os.path.getmtime(md_path)
                if mtime != last_mtime:
                    last_mtime = mtime
                    print(f'\n변경 감지 → 재빌드...')
                    build_html(md_path, out_path)
        except KeyboardInterrupt:
            print('\n종료')

if __name__ == '__main__':
    main()
