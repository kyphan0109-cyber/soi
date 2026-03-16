# This was made by AGAJAYOFFICIAL
from flask import Flask, jsonify, Response
import aiohttp
import asyncio
import json
import ssl
import sys
import base64
import threading
import time
import queue
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from byte import encrypt_api, Encrypt_ID
from visit_count_pb2 import Info
from Pb2 import MajoRLoGinrEq_pb2, MajoRLoGinrEs_pb2

app = Flask(__name__)

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
_AES_KEY    = b'Yg&tc%DEuh6%Zc^8'
_AES_IV     = b'6oyZDr22E3ychjM%'
CONCURRENT  = 1000
CHECK_EVERY = 120
SPINNER     = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
TOKEN_FILE  = "token_vn.json"
ACCOUNT_FILE= "accounts.json"

Hr = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB52"
}

# ──────────────────────────────────────────
# LOG QUEUE (gửi log lên /console)
# ──────────────────────────────────────────
log_queue = queue.Queue(maxsize=500)

def log(msg: str):
    now = datetime.now().strftime("%H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    try:
        log_queue.put_nowait(line)
    except queue.Full:
        try: log_queue.get_nowait()
        except: pass
        log_queue.put_nowait(line)

# ──────────────────────────────────────────
# SPINNER
# ──────────────────────────────────────────
class SpinnerStatus:
    def __init__(self):
        self.total   = 0
        self.success = 0
        self.failed  = 0
        self.running = False
        self._task   = None

    def start(self, total):
        self.total   = total
        self.success = 0
        self.failed  = 0
        self.running = True
        self._task   = asyncio.create_task(self._spin())

    async def stop(self):
        self.running = False
        if self._task:
            await self._task
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    async def _spin(self):
        i = 0
        while self.running:
            frame = SPINNER[i % len(SPINNER)]
            done  = self.success + self.failed
            line  = (
                f"\r{frame} Đang lấy token... "
                f"✅ {self.success} "
                f"❌ {self.failed} "
                f"/ {self.total} "
                f"[{done}/{self.total}]"
            )
            sys.stdout.write(line)
            sys.stdout.flush()
            # cũng push lên console web
            log_queue.put_nowait(
                f"⠿ Lấy token... ✅ {self.success} ❌ {self.failed} / {self.total}"
            )
            await asyncio.sleep(0.5)
            i += 1

spinner = SpinnerStatus()

# ──────────────────────────────────────────
# TOKEN HELPERS
# ──────────────────────────────────────────
def is_token_live(token: str) -> bool:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return time.time() < data.get("exp", 0)
    except:
        return False

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

_file_lock = asyncio.Lock()

async def append_token_vn(token: str):
    async with _file_lock:
        data = load_json(TOKEN_FILE)
        data.append({"token": token})
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

async def clear_token_file():
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# ──────────────────────────────────────────
# GET TOKEN
# ──────────────────────────────────────────
async def GeNeRaTeAccEss(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    data = {
        "uid": uid, "password": password,
        "response_type": "token", "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=Hr, data=data) as r:
            if r.status != 200: return None, None
            j = await r.json(content_type=None)
            return j.get("open_id"), j.get("access_token")

async def EncRypTMajoRLoGin(open_id, access_token):
    ml = MajoRLoGinrEq_pb2.MajorLogin()
    ml.event_time = str(datetime.now())[:-7]
    ml.game_name = "free fire"
    ml.platform_id = 1
    ml.client_version = "1.120.2"
    ml.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    ml.system_hardware = "Handheld"
    ml.telecom_operator = "Verizon"
    ml.network_type = "WIFI"
    ml.screen_width = 1920
    ml.screen_height = 1080
    ml.screen_dpi = "280"
    ml.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    ml.memory = 3003
    ml.gpu_renderer = "Adreno (TM) 640"
    ml.gpu_version = "OpenGL ES 3.1 v1.46"
    ml.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    ml.client_ip = "223.191.51.89"
    ml.language = "en"
    ml.open_id = open_id
    ml.open_id_type = "4"
    ml.device_type = "Handheld"
    ml.memory_available.version = 55
    ml.memory_available.hidden_value = 81
    ml.access_token = access_token
    ml.platform_sdk_id = 1
    ml.network_operator_a = "Verizon"
    ml.network_type_a = "WIFI"
    ml.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    ml.external_storage_total = 36235
    ml.external_storage_available = 31335
    ml.internal_storage_total = 2519
    ml.internal_storage_available = 703
    ml.game_disk_storage_available = 25010
    ml.game_disk_storage_total = 26628
    ml.external_sdcard_avail_storage = 32992
    ml.external_sdcard_total_storage = 36235
    ml.login_by = 3
    ml.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    ml.reg_avatar = 1
    ml.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    ml.channel_type = 3
    ml.cpu_type = 2
    ml.cpu_architecture = "64"
    ml.client_version_code = "2019116753"
    ml.graphics_api = "OpenGLES2"
    ml.supported_astc_bitset = 16383
    ml.login_open_id_type = 4
    ml.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    ml.loading_time = 13564
    ml.release_channel = "android"
    ml.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    ml.android_engine_init_flag = 110009
    ml.if_push = 1
    ml.is_vpn = 1
    ml.origin_platform_type = "4"
    ml.primary_platform_type = "4"
    cipher = AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV)
    return cipher.encrypt(pad(ml.SerializeToString(), AES.block_size))

async def MajorLogin(payload):
    url = "https://loginbp.ggblueshark.com/MajorLogin"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as s:
        async with s.post(url, data=payload, headers=Hr, ssl=ctx) as r:
            return await r.read() if r.status == 200 else None

async def DecRypTMajoRLoGin(raw):
    proto = MajoRLoGinrEs_pb2.MajorLoginRes()
    proto.ParseFromString(raw)
    return proto

async def GetToken(uid, password, semaphore):
    async with semaphore:
        for _ in range(9999):
            try:
                open_id, access_token = await GeNeRaTeAccEss(str(uid), password)
                if not open_id or not access_token:
                    await asyncio.sleep(0.5)
                    continue
                payload = await EncRypTMajoRLoGin(open_id, access_token)
                raw     = await MajorLogin(payload)
                if not raw:
                    await asyncio.sleep(0.5)
                    continue
                auth = await DecRypTMajoRLoGin(raw)
                if not auth.token:
                    await asyncio.sleep(0.5)
                    continue
                await append_token_vn(auth.token)
                spinner.success += 1
                return auth.token
            except:
                await asyncio.sleep(0.5)
        spinner.failed += 1
        return None

async def refresh_tokens(accounts):
    total     = len(accounts)
    semaphore = asyncio.Semaphore(CONCURRENT)
    await clear_token_file()
    log(f"🚀 Bắt đầu lấy token {total} tài khoản ({CONCURRENT} luồng)...")
    spinner.start(total)
    tasks = [
        GetToken(acc["uid"], acc["password"], semaphore)
        for acc in accounts
        if acc.get("uid") and acc.get("password")
    ]
    await asyncio.gather(*tasks)
    await spinner.stop()
    log(f"✅ Xong! {spinner.success} thành công | ❌ {spinner.failed} thất bại")
    log(f"💾 Đã lưu vào {TOKEN_FILE}")

# ──────────────────────────────────────────
# AUTO REFRESH LOOP
# ──────────────────────────────────────────
async def auto_refresh_loop():
    while True:
        log(f"📋 Checking {TOKEN_FILE}...")
        tokens = load_json(TOKEN_FILE)
        total  = len(tokens)

        if total > 0:
            die_count  = sum(1 for t in tokens if not is_token_live(t.get("token", "")))
            live_count = total - die_count
            log(f"📊 Tổng: {total} | ✅ Live: {live_count} | ❌ Die: {die_count}")

            if die_count <= total / 3:
                log(f"✅ Token còn đủ — chờ {CHECK_EVERY}s...")
                await asyncio.sleep(CHECK_EVERY)
                continue

            log(f"🚨 Die {die_count}/{total} > 1/3 — Refresh!")
        else:
            log("⚠️ token_vn.json rỗng — lấy mới!")

        accounts = load_json(ACCOUNT_FILE)
        if not accounts:
            log("❌ accounts.json rỗng!")
            await asyncio.sleep(CHECK_EVERY)
            continue

        await refresh_tokens(accounts)
        log(f"⏳ Chờ {CHECK_EVERY}s rồi check lại...")
        await asyncio.sleep(CHECK_EVERY)

# ──────────────────────────────────────────
# FLASK ROUTES
# ──────────────────────────────────────────
def load_tokens(server_name):
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
        return [item["token"] for item in data if "token" in item and item["token"] not in ["", "N/A"]]
    except Exception as e:
        app.logger.error(f"❌ Token load error: {e}")
        return []

def parse_protobuf_response(response_data):
    try:
        info = Info()
        info.ParseFromString(response_data)
        return {
            "uid":      info.AccountInfo.UID or 0,
            "nickname": info.AccountInfo.PlayerNickname or "",
            "likes":    info.AccountInfo.Likes or 0,
            "region":   info.AccountInfo.PlayerRegion or "",
            "level":    info.AccountInfo.Levels or 0
        }
    except Exception as e:
        app.logger.error(f"❌ Protobuf parsing error: {e}")
        return None

async def visit(session, url, token, uid, data):
    headers = {
        "ReleaseVersion": "OB52",
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "Host": url.replace("https://", "").split("/")[0]
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.post(url, headers=headers, data=data, ssl=False, timeout=timeout) as resp:
            if resp.status == 200:
                return True, await resp.read()
            return False, None
    except Exception as e:
        return False, None

async def send_until_50000_success(tokens, uid, target_success=50000):
    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    connector = aiohttp.TCPConnector(limit=0)
    total_success = 0
    total_sent    = 0
    player_info   = None

    try:
        encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
        data = bytes.fromhex(encrypted)
    except Exception as e:
        log(f"❌ Encrypt error: {e}")
        return 0, 0, None

    async with aiohttp.ClientSession(connector=connector) as session:
        while total_success < target_success:
            batch_size = min(target_success - total_success, 3000)
            tasks = [
                asyncio.create_task(
                    visit(session, url, tokens[(total_sent + i) % len(tokens)], uid, data)
                )
                for i in range(batch_size)
            ]
            results = await asyncio.gather(*tasks)

            if player_info is None:
                for success, response in results:
                    if success and response:
                        player_info = parse_protobuf_response(response)
                        break

            batch_success  = sum(1 for r, _ in results if r)
            total_success += batch_success
            total_sent    += batch_size
            log(f"[Visit] uid={uid} | batch={batch_size} | ok={batch_success} | total={total_success}/{target_success}")

    return total_success, total_sent, player_info

# ── /console HTML ────────────────────────
@app.route('/console')
def console_page():
    return Response("""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Console Log</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0d0d0d; color: #00ff99; font-family: 'Courier New', monospace; height: 100vh; display: flex; flex-direction: column; }
  #header { background: #111; padding: 12px 20px; border-bottom: 1px solid #00ff9933; display: flex; align-items: center; gap: 12px; }
  #header h1 { font-size: 16px; color: #00ff99; letter-spacing: 2px; }
  #status { width: 10px; height: 10px; border-radius: 50%; background: #00ff99; animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  #console { flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 4px; }
  .line { font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-all; animation: fadeIn 0.2s ease; }
  @keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
  .line.ok   { color: #00ff99; }
  .line.err  { color: #ff4444; }
  .line.warn { color: #ffaa00; }
  .line.info { color: #44aaff; }
  .line.spin { color: #cc88ff; }
  #footer { background: #111; padding: 8px 20px; border-top: 1px solid #00ff9933; font-size: 11px; color: #555; display: flex; justify-content: space-between; }
  #clear-btn { background: #1a1a1a; border: 1px solid #00ff9944; color: #00ff99; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; }
  #clear-btn:hover { background: #00ff9922; }
</style>
</head>
<body>
<div id="header">
  <div id="status"></div>
  <h1>⚡ CONSOLE LOG</h1>
  <button id="clear-btn" onclick="clearConsole()">🗑 Clear</button>
</div>
<div id="console" id="log"></div>
<div id="footer">
  <span id="count">0 dòng</span>
  <span>Auto-scroll: ON</span>
</div>

<script>
const box   = document.getElementById('console');
const count = document.getElementById('count');
let total   = 0;
let autoScroll = true;

box.addEventListener('scroll', () => {
  autoScroll = box.scrollHeight - box.scrollTop - box.clientHeight < 50;
});

function getClass(text) {
  if (text.includes('✅') || text.includes('Xong') || text.includes('Live') || text.includes('lưu')) return 'ok';
  if (text.includes('❌') || text.includes('error') || text.includes('Error') || text.includes('lỗi')) return 'err';
  if (text.includes('⚠️') || text.includes('🚨') || text.includes('Die')) return 'warn';
  if (text.includes('⠿') || text.includes('token...')) return 'spin';
  return 'info';
}

function addLine(text) {
  // cập nhật dòng spinner thay vì thêm mới
  if (text.includes('⠿')) {
    let existing = document.getElementById('spinner-line');
    if (!existing) {
      existing = document.createElement('div');
      existing.id = 'spinner-line';
      existing.className = 'line spin';
      box.appendChild(existing);
    }
    existing.textContent = text;
  } else {
    const div = document.createElement('div');
    div.className = 'line ' + getClass(text);
    div.textContent = text;
    box.appendChild(div);
    total++;
    count.textContent = total + ' dòng';
  }
  if (autoScroll) box.scrollTop = box.scrollHeight;
}

function clearConsole() {
  box.innerHTML = '';
  total = 0;
  count.textContent = '0 dòng';
}

// SSE stream
const es = new EventSource('/console/stream');
es.onmessage = e => addLine(e.data);
es.onerror   = () => addLine('[❌ Mất kết nối — đang thử lại...]');
</script>
</body>
</html>""", mimetype="text/html")

# ── /console/stream SSE ──────────────────
@app.route('/console/stream')
def console_stream():
    def generate():
        while True:
            try:
                msg = log_queue.get(timeout=30)
                yield f"data: {msg}\n\n"
            except queue.Empty:
                yield "data: ⏳ Đang chờ...\n\n"
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ── /tokens ──────────────────────────────
@app.route('/tokens', methods=['GET'])
def check_tokens():
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
        valid   = [i["token"] for i in data if "token" in i and i["token"] not in ["", "N/A"]]
        live    = sum(1 for t in valid if is_token_live(t))
        return jsonify({"file": TOKEN_FILE, "total": len(data), "valid": len(valid), "live": live, "die": len(valid) - live}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── /VN/<uid> ────────────────────────────
@app.route('/VN/<int:uid>', methods=['GET'])
def send_visits(uid):
    tokens = load_tokens("VN")
    if not tokens:
        return jsonify({"error": "❌ No valid tokens found"}), 500
    log(f"🚀 Visit uid={uid} | {len(tokens)} tokens")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        total_success, total_sent, player_info = loop.run_until_complete(
            send_until_50000_success(tokens, uid)
        )
    finally:
        loop.close()
    if player_info:
        return jsonify({
            "fail":     50000 - total_success,
            "level":    player_info.get("level", 0),
            "likes":    player_info.get("likes", 0),
            "nickname": player_info.get("nickname", ""),
            "region":   player_info.get("region", ""),
            "success":  total_success,
            "uid":      player_info.get("uid", 0)
        }), 200
    return jsonify({"error": "Could not decode player information"}), 500

# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
if __name__ == "__main__":
    def start_refresh():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(auto_refresh_loop())

    threading.Thread(target=start_refresh, daemon=True).start()
    app.run(host="0.0.0.0", port=5090, threaded=True)
