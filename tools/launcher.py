"""動作確認用のランチャー: ブラウザのページから、各テストプログラムを起動する。

python tools/launcher.py        → http://127.0.0.1:8765/ がブラウザで開く
python tools/launcher.py --python C:/path/to/python.exe   起動に使う Python を指定する

起動に使う Python: このランチャーを動かした Python に Pyxel が入っていればそれを使う。入っていなければ、
Anaconda の環境(envs)や PATH 上の Python から Pyxel の入っているものを探して使う(環境変数 STARX_PYTHON でも指定できる)。

ブラウザは手元のプログラムを直接は起動できないので、このスクリプトが小さな Web サーバーになって、
ページのボタンが押されたらプログラムを起動する。自分の PC(127.0.0.1)からしか開けない。
起動できるのは下の PROGRAMS に書いたものだけで、引数も決まった値しか受け付けない。
終了は、このスクリプトを動かしている端末で Ctrl+C。
"""

import glob
import html
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game import script  # noqa: E402
from game.i18n import LANGS  # noqa: E402
from game.missions import ORDER  # noqa: E402

# game/ui.py の SCREENS と同じ(ランチャー自体は Pyxel なしでも動くように、ここに書く)
SCREENS = ("640x480", "720x720", "360x360", "320x240")

PORT = 8765
SHOTS = ROOT / "tools" / "shots"
# 会話の挿絵。番号(game/script.py の IMAGES)が 6-1 なら s06_1_*.png、2 なら s02_*.png
ILLUST = ROOT / "assets" / "illustrations"
ILLUST_TYPES = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg"}
STAGES = [(m.id, m.title) for m in ORDER]

NEEDS_PYXEL = {"game", "flight", "autoplay"}  # Pyxel がないと動かないもの

# 起動できるプログラム。console: 別の端末ウィンドウで動かす(文字で出力・入力するもの)
PROGRAMS = {
    "game": dict(script="main.py", console=False),
    "flight": dict(script="tools/flight_test.py", console=False),
    "story": dict(script="tools/story_check.py", console=True),
    "read": dict(script="tools/story_read.py", capture=True),
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
    if lang in LANGS and prog in ("game", "flight", "story", "read", "autoplay"):
        args.append(lang)
    if stage in {s for s, _ in STAGES} and prog in ("game", "story", "read", "sim", "autoplay"):
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


def has_pyxel(python):
    """その Python に Pyxel が入っているか。"""
    if os.path.normcase(os.path.abspath(python)) == os.path.normcase(os.path.abspath(sys.executable)):
        return importlib.util.find_spec("pyxel") is not None
    try:
        out = subprocess.run([python, "-c", "import importlib.util as u; print(bool(u.find_spec('pyxel')))"],
                             capture_output=True, text=True, timeout=20)
        return out.stdout.strip() == "True"
    except (OSError, subprocess.SubprocessError):
        return False


def candidate_pythons():
    """Pyxel が入っていそうな Python の候補(先に見るものほど優先)。"""
    exe = "python.exe" if os.name == "nt" else os.path.join("bin", "python")
    found = [sys.executable]
    # Anaconda / Miniconda の環境: いまの環境の envs と、いまが envs の中ならその兄弟
    prefixes = {sys.prefix, os.environ.get("CONDA_PREFIX", ""), os.path.dirname(os.environ.get("CONDA_EXE", ""))}
    roots = set()
    for prefix in filter(None, prefixes):
        prefix = os.path.abspath(prefix)
        if os.path.basename(os.path.dirname(prefix)) == "envs":
            roots.add(os.path.dirname(prefix))
        roots.add(os.path.join(prefix, "envs"))
        roots.add(os.path.join(os.path.dirname(prefix), "envs"))  # CONDA_EXE は Scripts の中
    envs = sorted(p for root in roots for p in glob.glob(os.path.join(root, "*", exe)))
    # 名前に pyxel が入っている環境を先に
    envs.sort(key=lambda p: "pyxel" not in p.lower())
    found += envs
    for name in ("python", "python3"):
        path = shutil.which(name)
        if path:
            found.append(path)
    seen, result = set(), []
    for p in found:
        key = os.path.normcase(os.path.abspath(p))
        if key not in seen and os.path.exists(p):
            seen.add(key)
            result.append(p)
    return result


def find_python():
    """ゲームの起動に使う Python。指定(--python / STARX_PYTHON)があればそれ、なければ Pyxel の入ったものを探す。"""
    if "--python" in sys.argv:
        i = sys.argv.index("--python")
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    if os.environ.get("STARX_PYTHON"):
        return os.environ["STARX_PYTHON"]
    for python in candidate_pythons():
        if has_pyxel(python):
            return python
    return None


PYTHON = None  # main() で決める


def launch(prog, opts):
    """プログラムを起動する。(ok, メッセージ, 出力) を返す。"""
    spec = PROGRAMS.get(prog)
    if not spec:
        return False, "知らないプログラムです", ""
    python = PYTHON or sys.executable
    if PYTHON is None and prog in NEEDS_PYXEL:
        return False, ("Pyxel の入った Python が見つかりません。pip install pyxel するか、"
                       "python tools/launcher.py --python <Pyxel の入った python.exe> で起動してください"), ""
    cmd = [python, str(ROOT / spec["script"])] + build_args(prog, opts)
    shown = " ".join(["python", spec["script"]] + cmd[2:])
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if spec.get("capture"):
        out = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=120)
        return out.returncode == 0, shown, (out.stdout + out.stderr).strip()
    if spec.get("console"):
        if os.name == "nt":
            # 新しい端末ウィンドウで動かし、終わっても閉じずに結果を読めるようにする
            subprocess.Popen(["cmd", "/k"] + cmd, cwd=ROOT, env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(cmd, cwd=ROOT, env=env)  # 出力はランチャーを動かしている端末に出る
        return True, shown, ""
    # ウィンドウの開くもの: すぐに落ちたら、そのエラーをページに返す
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                            errors="replace")
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        threading.Thread(target=proc.stderr.read, daemon=True).start()  # 動き続けている。出力は読み捨てる
        return True, shown, ""
    err = proc.stderr.read().strip()
    if proc.returncode != 0:
        return False, f"起動してすぐに終了しました(終了コード {proc.returncode}): {shown}", err
    return True, shown, err


def list_shots():
    """tools/shots のスクリーンショット: {フォルダ: [ファイル名, ...]}(新しい順)。"""
    result = {}
    if SHOTS.exists():
        for folder in sorted(p for p in SHOTS.iterdir() if p.is_dir()):
            files = sorted(folder.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                result[folder.name] = [f.name for f in files]
    return result


def illust_prefix(num):
    """挿絵の番号からファイル名の頭を作る: 6-1 → s06_1_、2 → s02_。"""
    major, _, minor = num.partition("-")
    return f"s{int(major):02d}_" + (f"{minor}_" if minor else "")


def illust_file(num):
    """挿絵のファイル。その番号の絵がなければ親の番号の絵(9-1 なら 9)を使う。なければ None。"""
    while True:
        files = sorted(f for f in ILLUST.glob(illust_prefix(num) + "*") if f.suffix.lower() in ILLUST_TYPES)
        if files:
            return files[0]
        if "-" not in num:
            return None
        num = num.rsplit("-", 1)[0]


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
        if path.startswith("/illust/"):
            return self.illust(path[len("/illust/"):])
        self.send(404, "not found", "text/plain; charset=utf-8")

    def illust(self, num):
        """挿絵を出す。まだなければ、どこに置けばよいかを出す。"""
        if num not in script.IMAGES:
            return self.send(404, "not found", "text/plain; charset=utf-8")
        target = illust_file(num)
        if target:
            return self.send(200, target.read_bytes(), ILLUST_TYPES[target.suffix.lower()])
        body = (f"<!doctype html><meta charset='utf-8'><title>挿絵 {html.escape(num)}</title>"
                f"<body style='font-family:sans-serif;padding:24px'><h1>挿絵 {html.escape(num)}: "
                f"{html.escape(script.IMAGES[num])}</h1><p>まだ画像がありません。"
                f"<code>assets/illustrations/{html.escape(illust_prefix(num))}*.png</code> に置くと、ここに表示されます。</p></body>")
        return self.send(200, body, "text/html; charset=utf-8")

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
        card("read", "会話の通し読み", "全部の打ち上げが成功したことにして、各ステージの会話を順に出す。選択肢なし。結果はこのページに出る。",
             field("開始", options("stage", stages)) + field("言語", options("lang", langs))),
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
dialog.read { width:min(1000px, 94vw); height:92vh; padding:0; border:1px solid var(--line); border-radius:12px; background:var(--card); color:var(--text); }
dialog.read::backdrop { background:rgba(0,0,0,.45); }
.read-wrap { display:flex; flex-direction:column; height:100%; }
.read-bar { display:flex; gap:10px; align-items:center; padding:10px 16px; border-bottom:1px solid var(--line); flex-wrap:wrap; }
.read-bar strong { font-size:15px; }
.read-bar select { max-width:260px; }
.read-bar button { margin-left:auto; }
.read-body { overflow:auto; padding:8px 28px 40px; font-size:16px; line-height:1.8; }
.read-body h2 { font-size:18px; margin:28px 0 6px; padding-bottom:4px; border-bottom:2px solid var(--accent); }
.read-body h4 { font-size:12px; color:var(--muted); margin:14px 0 2px; font-weight:600; letter-spacing:.05em; }
.read-body .ln { display:grid; grid-template-columns:7.5em 1fr; gap:12px; padding:1px 0; }
.read-body .who { color:var(--accent); font-weight:600; text-align:right; white-space:nowrap; }
.read-body .nar { color:var(--muted); font-style:italic; padding:2px 0 2px calc(7.5em + 12px); }
.read-body .img { margin:8px 0 8px calc(7.5em + 12px); }
.read-body .img a { display:inline-block; padding:3px 10px; border:1px dashed var(--accent); border-radius:6px; color:var(--accent); text-decoration:none; font-size:14px; }
.read-body .img a:hover { background:var(--code); }
dialog.illust { max-width:96vw; max-height:94vh; padding:0; border:0; border-radius:10px; background:#000; color:#eee; overflow:hidden; }
dialog.illust::backdrop { background:rgba(0,0,0,.7); }
dialog.illust img { display:block; max-width:96vw; max-height:calc(94vh - 40px); image-rendering:pixelated; cursor:zoom-out; }
dialog.illust .cap { display:flex; gap:12px; align-items:center; padding:8px 12px; font-size:14px; }
dialog.illust .cap button { margin-left:auto; font-size:12px; padding:3px 10px; }
dialog.illust .missing { padding:40px 32px; font-size:15px; }
@media (max-width:600px) { .read-body { padding:8px 14px 32px; } .read-body .ln { grid-template-columns:1fr; gap:0; } .read-body .who { text-align:left; }
  .read-body .nar, .read-body .img { padding-left:0; margin-left:0; } }
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
<dialog class="read" id="read">
  <div class="read-wrap">
    <div class="read-bar"><strong>会話の通し読み</strong><select id="read-jump"></select><button type="button" id="read-close">閉じる(Esc)</button></div>
    <div class="read-body" id="read-body"></div>
  </div>
</dialog>
<dialog class="illust" id="illust">
  <img id="illust-img" alt="">
  <p class="missing" id="illust-missing" hidden></p>
  <div class="cap"><span id="illust-cap"></span><button type="button" id="illust-close">閉じる(Esc)</button></div>
</dialog>
<script>
// 挿絵を、通し読みの上にポップアップで出す
function showIllust(num, label) {
  const dlg = document.getElementById('illust'), img = document.getElementById('illust-img'), miss = document.getElementById('illust-missing');
  document.getElementById('illust-cap').textContent = '画像 ' + num + ': ' + label;
  img.hidden = false; miss.hidden = true;
  img.onerror = () => {
    const [major, minor] = num.split('-');
    img.hidden = true; miss.hidden = false;
    miss.textContent = 'まだ画像がありません。assets/illustrations/s' + major.padStart(2, '0') + '_' + (minor ? minor + '_' : '') + '*.png に置くと表示されます。';
  };
  img.src = '/illust/' + encodeURIComponent(num);
  if (!dlg.open) dlg.showModal();
}
document.getElementById('illust').addEventListener('click', e => { if (e.target.id !== 'illust-cap') document.getElementById('illust').close(); });
// Esc で挿絵だけを閉じる(下の通し読みまで閉じない)
document.addEventListener('keydown', e => {
  const il = document.getElementById('illust');
  if (e.key === 'Escape' && il.open) { e.preventDefault(); e.stopPropagation(); il.close(); }
}, true);
// 会話の通し読みの結果を、読みやすい形にしてポップアップで出す
function showRead(text) {
  const body = document.getElementById('read-body'), jump = document.getElementById('read-jump');
  body.innerHTML = ''; jump.innerHTML = '<option value="">ステージへ移動…</option>';
  const add = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; body.appendChild(e); return e; };
  let n = 0, m;
  for (const line of text.split(String.fromCharCode(10))) {
    if ((m = line.match(/^==== (.*) ====$/))) {
      const h = add('h2', '', m[1]); h.id = 'sec' + (n++);
      jump.add(new Option(m[1], h.id));
    } else if ((m = line.match(/^  -- (.*) --$/))) {
      add('h4', '', m[1]);
    } else if ((m = line.match(/^  【画像 ([^:】 ]+): ([^】]*)】$/))) {
      const a = document.createElement('a'); a.href = '/illust/' + encodeURIComponent(m[1]);
      const num = m[1], label = m[2];
      a.addEventListener('click', e => { e.preventDefault(); showIllust(num, label); });
      a.textContent = '画像 ' + m[1] + ': ' + m[2]; add('div', 'img').appendChild(a);
    } else if ((m = line.match(/^  ([^「(]+)「(.*)」$/))) {
      const row = add('div', 'ln'); const w = document.createElement('span'); w.className = 'who'; w.textContent = m[1];
      const t = document.createElement('span'); t.textContent = m[2]; row.append(w, t);
    } else if (line.startsWith('  (') && line.endsWith(')')) {
      add('div', 'nar', line.slice(3, -1));
    } else if (line.trim()) {
      add('div', 'nar', line.trim());
    }
  }
  const dlg = document.getElementById('read');
  if (!dlg.open) dlg.showModal();
  body.scrollTop = 0;
}
document.getElementById('read-jump').addEventListener('change', e => {
  const t = document.getElementById(e.target.value); if (t) t.scrollIntoView({block:'start'}); e.target.value = '';
});
document.getElementById('read-close').addEventListener('click', () => document.getElementById('read').close());
let lastRead = '';
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
      if (r.out && card.dataset.prog === 'read') {
        lastRead = r.out;
        showRead(r.out);
        if (!card.querySelector('.reopen')) {
          const b = document.createElement('button'); b.type = 'button'; b.className = 'reopen'; b.textContent = 'もう一度開く';
          b.addEventListener('click', () => showRead(lastRead)); card.querySelector('.row').appendChild(b);
        }
      } else if (r.out) {
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
    global PYTHON
    PYTHON = find_python()
    if PYTHON:
        print(f"ゲームの起動に使う Python: {PYTHON}", flush=True)
    else:
        print("Pyxel の入った Python が見つかりません。ゲームを起動するボタンは動きません。", flush=True)
        print("  pip install pyxel するか、--python <Pyxel の入った python.exe> を付けて起動してください。", flush=True)
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
