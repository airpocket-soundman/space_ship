"""動作確認用のランチャー: ブラウザのページから、各テストプログラムを起動する。

python tools/launcher.py        → http://127.0.0.1:8765/ がブラウザで開く

ブラウザは手元のプログラムを直接は起動できないので、このスクリプトが小さな Web サーバーになって、
ページのボタンが押されたらプログラムを起動する。自分の PC(127.0.0.1)からしか開けない。
起動できるのは下の PROGRAMS に書いたものだけで、引数も決まった値しか受け付けない。
終了は、このスクリプトを動かしている端末で Ctrl+C。
"""

import html
import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.i18n import LANGS  # noqa: E402
from game.missions import ORDER  # noqa: E402

# game/ui.py の SCREENS と同じ(ランチャー自体は Pyxel なしでも動くように、ここに書く)
SCREENS = ("640x480", "720x720", "360x360", "320x240")

PORT = 8765
SHOTS = ROOT / "tools" / "shots"
STAGES = [(m.id, m.title) for m in ORDER]

# 起動できるプログラム。console: 別の端末ウィンドウで動かす(文字で出力・入力するもの)
PROGRAMS = {
    "game": dict(script="main.py", console=False),
    "flight": dict(script="tools/flight_test.py", console=False),
    "story": dict(script="tools/story_check.py", console=True),
    "sim": dict(script="tools/sim_check.py", console=True),
    "autoplay": dict(script="tools/autoplay.py", console=True),
    "i18n": dict(script="tools/check_i18n.py", capture=True),
}


def build_args(prog, opts):
    """ページから来た設定を、決まった値だけのコマンドライン引数にする。"""
    args = []
    screen = opts.get("screen")
    lang = opts.get("lang")
    stage = opts.get("stage") or ""
    if screen in SCREENS and prog in ("game", "flight", "autoplay"):
        args.append(screen)
    if lang in LANGS and prog in ("game", "flight", "story", "autoplay"):
        args.append(lang)
    if stage in {s for s, _ in STAGES} and prog in ("game", "story", "sim", "autoplay"):
        args.append(stage)
    flags = {
        "flight": {"mute": "mute"},
        "story": {"auto": "--auto", "step": "--step"},
        "sim": {"verbose": "-v"},
        "autoplay": {"fast": "--fast", "inspect": "--inspect", "sound": "--sound", "quick": "--quick"},
    }.get(prog, {})
    for key, flag in flags.items():
        if opts.get(key) is True:
            args.append(flag)
    return args


def launch(prog, opts):
    """プログラムを起動する。(ok, メッセージ, 出力) を返す。"""
    spec = PROGRAMS.get(prog)
    if not spec:
        return False, "知らないプログラムです", ""
    cmd = [sys.executable, str(ROOT / spec["script"])] + build_args(prog, opts)
    shown = " ".join(["python", spec["script"]] + cmd[2:])
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if spec.get("capture"):
        out = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=120)
        return True, shown, (out.stdout + out.stderr).strip()
    if spec.get("console"):
        if os.name == "nt":
            # 新しい端末ウィンドウで動かし、終わっても閉じずに結果を読めるようにする
            subprocess.Popen(["cmd", "/k"] + cmd, cwd=ROOT, env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(cmd, cwd=ROOT, env=env)  # 出力はランチャーを動かしている端末に出る
        return True, shown, ""
    subprocess.Popen(cmd, cwd=ROOT, env=env)
    return True, shown, ""


def list_shots():
    """tools/shots のスクリーンショット: {フォルダ: [ファイル名, ...]}(新しい順)。"""
    result = {}
    if SHOTS.exists():
        for folder in sorted(p for p in SHOTS.iterdir() if p.is_dir()):
            files = sorted(folder.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                result[folder.name] = [f.name for f in files]
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # アクセスのたびに端末へ出さない
        pass

    def send(self, code, body, ctype):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/":
            return self.send(200, page(), "text/html; charset=utf-8")
        if path == "/api/shots":
            return self.send(200, json.dumps(list_shots(), ensure_ascii=False), "application/json; charset=utf-8")
        if path.startswith("/shots/"):
            target = (SHOTS / path[len("/shots/"):]).resolve()
            if target.is_file() and SHOTS.resolve() in target.parents and target.suffix == ".png":
                return self.send(200, target.read_bytes(), "image/png")
        self.send(404, "not found", "text/plain; charset=utf-8")

    def do_POST(self):
        if urlparse(self.path).path != "/api/run":
            return self.send(404, "not found", "text/plain; charset=utf-8")
        try:
            length = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(min(length, 10_000)) or b"{}")
            ok, msg, out = launch(str(req.get("prog")), req.get("opts") or {})
        except Exception as e:  # 起動に失敗しても、ページに理由を返す
            ok, msg, out = False, f"起動できませんでした: {e}", ""
        self.send(200, json.dumps({"ok": ok, "cmd": msg, "out": out}, ensure_ascii=False),
                  "application/json; charset=utf-8")


def options(name, values, selected=None):
    return f'<select name="{name}">' + "".join(
        f'<option value="{html.escape(v)}"{" selected" if v == selected else ""}>{html.escape(label)}</option>'
        for v, label in values) + "</select>"


def page():
    screens = [(s, s) for s in SCREENS]
    langs = [("ja", "日本語"), ("en", "English")]
    stages = [("", "最初から")] + [(s, t) for s, t in STAGES]
    stages_req = [(s, t) for s, t in STAGES]
    stages_all = [("", "全ステージ")] + [(s, t) for s, t in STAGES]

    def card(prog, title, desc, fields, note=""):
        return f"""
<section class="card" data-prog="{prog}">
  <h2>{title}</h2>
  <p class="desc">{desc}</p>
  <div class="fields">{fields}</div>
  <div class="row"><button type="button">起動</button><code class="cmd"></code></div>
  {f'<p class="note">{note}</p>' if note else ''}
</section>"""

    def check(name, label, on=False):
        return f'<label class="chk"><input type="checkbox" name="{name}"{" checked" if on else ""}> {label}</label>'

    def field(label, control):
        return f'<label class="fld"><span>{label}</span>{control}</label>'

    cards = "".join([
        card("game", "ゲーム本体", "タイトル画面から遊ぶ。ステージを選ぶと、その直前の会社画面から始まる(セーブしない)。",
             field("画面", options("screen", screens, "640x480")) + field("言語", options("lang", langs))
             + field("開始", options("stage", stages))),
        card("flight", "飛行テスト", "メニューからステージを選んですぐ飛ぶ。←→ で点検あり・なし、飛行中 Q でメニューへ。",
             field("画面", options("screen", screens, "640x480")) + field("言語", options("lang", langs))
             + check("mute", "消音")),
        card("story", "ストーリー確認", "文字だけでシナリオを進める。別の端末ウィンドウで開く。コマンドと飛行の成否を番号で選ぶ。",
             field("開始", options("stage", stages)) + field("言語", options("lang", langs))
             + check("auto", "最後まで自動") + check("step", "1 行ずつ送る")),
        card("sim", "バランス確認", "自動操縦で各ステージを 20 回ずつ飛ばし、成功率を出す(全ステージだと数十分)。別の端末ウィンドウで開く。",
             field("ステージ", options("stage", stages_all, "1-1")) + check("verbose", "詳しく")),
        card("autoplay", "自動操作スクリーンショット", "ステージを自動操縦で通し、tools/shots に画面を保存する。終わったら下の一覧を更新。",
             field("ステージ", options("stage", stages_req, "1-1")) + field("画面", options("screen", screens, "640x480"))
             + field("言語", options("lang", langs)) + check("fast", "6 倍速", True) + check("inspect", "点検してから")
             + check("sound", "音を鳴らす"),
             "ステージを選ばずにオープニングからの流れを撮るときは、端末で python tools/autoplay.py を実行。"),
        card("i18n", "英語訳のチェック", "英語の訳が抜けている文言を探す。結果はこのページに出る。", ""),
    ])
    return PAGE.replace("{{CARDS}}", cards)


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StarX 動作確認</title>
<style>
:root { --bg:#f4f5f8; --card:#fff; --text:#1c2230; --muted:#5d6678; --line:#dfe3ea; --accent:#2b5fd9; --ok:#1d8a55; --ng:#c8352f; --code:#eef1f6; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#12151d; --card:#1b2030; --text:#e6e9f0; --muted:#98a1b4; --line:#2c3448; --accent:#7ea2ff; --ok:#5fd29a; --ng:#ff7d74; --code:#232a3d; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.6 system-ui, "Segoe UI", "Hiragino Sans", "Yu Gothic UI", sans-serif; }
main { max-width:1100px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:22px; margin:0 0 4px; }
.lead { color:var(--muted); margin:0 0 20px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:14px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; gap:8px; }
.card h2 { font-size:16px; margin:0; }
.desc, .note { color:var(--muted); margin:0; font-size:13px; }
.fields { display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; }
.fld { display:flex; gap:6px; align-items:center; font-size:13px; }
.fld span { color:var(--muted); }
select { font:inherit; font-size:13px; padding:3px 6px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--text); max-width:190px; }
.chk { font-size:13px; display:flex; gap:4px; align-items:center; }
.row { display:flex; gap:10px; align-items:center; margin-top:auto; }
button { font:inherit; font-size:14px; padding:6px 16px; border:0; border-radius:6px; background:var(--accent); color:#fff; cursor:pointer; }
button:hover { filter:brightness(1.1); }
code, pre { font-family:ui-monospace, Consolas, monospace; font-size:12px; }
.cmd { color:var(--muted); overflow-wrap:anywhere; }
pre.out { background:var(--code); border-radius:6px; padding:8px 10px; margin:0; max-height:220px; overflow:auto; white-space:pre-wrap; }
.ok { color:var(--ok); } .ng { color:var(--ng); }
h3 { font-size:16px; margin:28px 0 8px; display:flex; gap:10px; align-items:center; }
h3 button { font-size:12px; padding:3px 10px; }
.shots details { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 12px; margin-bottom:8px; }
.shots summary { cursor:pointer; font-weight:600; }
.thumbs { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:8px; margin-top:8px; }
.thumbs a { display:block; text-decoration:none; color:var(--muted); font-size:11px; overflow-wrap:anywhere; }
.thumbs img { width:100%; image-rendering:pixelated; border-radius:4px; border:1px solid var(--line); display:block; }
.empty { color:var(--muted); font-size:13px; }
</style>
</head>
<body>
<main>
  <h1>StarX 動作確認</h1>
  <p class="lead">ボタンを押すと、この PC でプログラムが起動します。ランチャーの終了は、起動した端末で Ctrl+C。</p>
  <div class="grid">{{CARDS}}</div>
  <h3>スクリーンショット(tools/shots) <button type="button" id="reload">一覧を更新</button></h3>
  <div class="shots" id="shots"><p class="empty">読み込み中…</p></div>
</main>
<script>
document.querySelectorAll('.card').forEach(card => {
  card.querySelector('button').addEventListener('click', async () => {
    const opts = {};
    card.querySelectorAll('select').forEach(s => opts[s.name] = s.value);
    card.querySelectorAll('input[type=checkbox]').forEach(c => opts[c.name] = c.checked);
    const cmd = card.querySelector('.cmd');
    let out = card.querySelector('pre.out');
    cmd.textContent = '起動中…'; cmd.className = 'cmd';
    try {
      const res = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'},
                                           body: JSON.stringify({prog: card.dataset.prog, opts})});
      const r = await res.json();
      cmd.textContent = (r.ok ? '起動: ' : '') + r.cmd;
      cmd.className = 'cmd ' + (r.ok ? 'ok' : 'ng');
      if (r.out) {
        if (!out) { out = document.createElement('pre'); out.className = 'out'; card.appendChild(out); }
        out.textContent = r.out;
      }
    } catch (e) {
      cmd.textContent = 'ランチャーに接続できません(tools/launcher.py は動いていますか)';
      cmd.className = 'cmd ng';
    }
  });
});
async function loadShots() {
  const box = document.getElementById('shots');
  try {
    const data = await (await fetch('/api/shots')).json();
    const dirs = Object.keys(data);
    if (!dirs.length) { box.innerHTML = '<p class="empty">まだありません。自動操作スクリーンショットを実行すると、ここに並びます。</p>'; return; }
    box.innerHTML = '';
    dirs.forEach((dir, i) => {
      const d = document.createElement('details');
      if (i === 0) d.open = true;
      const s = document.createElement('summary');
      s.textContent = dir + '(' + data[dir].length + ' 枚)';
      d.appendChild(s);
      const t = document.createElement('div'); t.className = 'thumbs';
      data[dir].forEach(f => {
        const a = document.createElement('a');
        a.href = '/shots/' + encodeURIComponent(dir) + '/' + encodeURIComponent(f); a.target = '_blank';
        const img = document.createElement('img'); img.loading = 'lazy'; img.src = a.href; img.alt = f;
        a.appendChild(img); a.appendChild(document.createTextNode(f)); t.appendChild(a);
      });
      d.appendChild(t); box.appendChild(d);
    });
  } catch (e) { box.innerHTML = '<p class="empty">一覧を読めませんでした。</p>'; }
}
document.getElementById('reload').addEventListener('click', loadShots);
loadShots();
</script>
</body>
</html>
"""


def main():
    port = PORT
    for p in range(PORT, PORT + 20):  # 使われていたら次の番号へ
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    else:
        print("空いているポートが見つかりませんでした")
        return
    url = f"http://127.0.0.1:{port}/"
    print(f"StarX 動作確認ランチャー: {url}  (終了は Ctrl+C)", flush=True)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
