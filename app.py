# This was made by AGAJAYOFFICIAL
from flask import Flask, jsonify
import aiohttp
import asyncio
import json
import traceback
from byte import encrypt_api, Encrypt_ID
from visit_count_pb2 import Info

app = Flask(__name__)


# ====================== ERROR HANDLER TOÀN CỤC ======================
@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "error": "Internal Server Error",
        "detail": str(e),
        "traceback": traceback.format_exc()
    }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404
# ====================================================================


def load_tokens(server_name):
    try:
        if server_name == "IND":
            path = "token_ind.json"
        elif server_name == "VN":
            path = "token_vn.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            path = "token_br.json"
        else:
            path = "token_bd.json"

        with open(path, "r") as f:
            data = json.load(f)

        tokens = [item["token"] for item in data if "token" in item and item["token"] not in ["", "N/A"]]
        return tokens
    except FileNotFoundError:
        app.logger.error(f"❌ Token file not found for server: {server_name}")
        return []
    except Exception as e:
        app.logger.error(f"❌ Token load error for {server_name}: {e}")
        return []


def get_url(server_name):
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name == "VN":
        return "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        return "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"


def parse_protobuf_response(response_data):
    try:
        info = Info()
        info.ParseFromString(response_data)
        player_data = {
            "uid": info.AccountInfo.UID if info.AccountInfo.UID else 0,
            "nickname": info.AccountInfo.PlayerNickname if info.AccountInfo.PlayerNickname else "",
            "likes": info.AccountInfo.Likes if info.AccountInfo.Likes else 0,
            "region": info.AccountInfo.PlayerRegion if info.AccountInfo.PlayerRegion else "",
            "level": info.AccountInfo.Levels if info.AccountInfo.Levels else 0
        }
        return player_data
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
            print(f"[DEBUG] Status: {resp.status} | URL: {url}")
            if resp.status == 200:
                response_data = await resp.read()
                return True, response_data
            else:
                body = await resp.text()
                print(f"[DEBUG] Non-200: {resp.status} — {body[:200]}")
                return False, None
    except asyncio.TimeoutError:
        print(f"⏱️ Timeout khi gửi request tới {url}")
        return False, None
    except aiohttp.ClientError as e:
        print(f"❌ Aiohttp client error: {type(e).__name__}: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Visit error detail: {type(e).__name__}: {e}")
        return False, None


async def send_until_10000_success(tokens, uid, server_name, target_success=10000):
    url = get_url(server_name)
    connector = aiohttp.TCPConnector(limit=0)
    total_success = 0
    total_sent = 0
    first_success_response = None
    player_info = None

    try:
        encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
        print(f"[DEBUG] Encrypted hex: {encrypted}")
        data = bytes.fromhex(encrypted)
        print(f"[DEBUG] Data bytes length: {len(data)}")
    except Exception as e:
        print(f"❌ Encrypt error: {type(e).__name__}: {e}")
        return 0, 0, None

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            while total_success < target_success:
                batch_size = min(target_success - total_success, 3000)
                tasks = [
                    asyncio.create_task(
                        visit(session, url, tokens[(total_sent + i) % len(tokens)], uid, data)
                    )
                    for i in range(batch_size)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Lọc bỏ exception, chỉ lấy tuple (bool, data)
                clean_results = [r for r in results if isinstance(r, tuple)]

                if first_success_response is None:
                    for success, response in clean_results:
                        if success and response is not None:
                            first_success_response = response
                            player_info = parse_protobuf_response(response)
                            break

                batch_success = sum(1 for r, _ in clean_results if r)
                total_success += batch_success
                total_sent += batch_size

                print(f"Batch sent: {batch_size}, Success: {batch_success}, Total: {total_success}")
    except Exception as e:
        print(f"❌ Session error: {type(e).__name__}: {e}")

    return total_success, total_sent, player_info


# ====================== ROUTE: XEM SỐ LƯỢNG TOKEN ======================
@app.route('/tokens', methods=['GET'])
def check_tokens():
    servers = {
        "IND": "token_ind.json",
        "VN": "token_vn.json",
        "BR/US/SAC/NA": "token_br.json",
        "BD (others)": "token_bd.json"
    }

    result = {}
    total_all = 0

    for label, path in servers.items():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            all_tokens = len(data)
            valid_tokens = [item["token"] for item in data if "token" in item and item["token"] not in ["", "N/A"]]
            valid_count = len(valid_tokens)
            invalid_count = all_tokens - valid_count
            total_all += valid_count
            result[label] = {
                "file": path,
                "total": all_tokens,
                "valid": valid_count,
                "invalid": invalid_count
            }
        except FileNotFoundError:
            result[label] = {"file": path, "error": "❌ File not found"}
        except Exception as e:
            result[label] = {"file": path, "error": str(e)}

    return jsonify({
        "servers": result,
        "total_valid_tokens": total_all
    }), 200
# ========================================================================


@app.route('/<string:server>/<int:uid>', methods=['GET'])
def send_visits(server, uid):
    try:
        server = server.upper()

        # Validate server
        valid_servers = {"IND", "VN", "BR", "US", "SAC", "NA", "BD", "SG", "TH", "ID", "MY", "PH", "TW", "ME", "PK"}
        if server not in valid_servers:
            return jsonify({"error": f"❌ Server '{server}' không hợp lệ"}), 400

        # Validate uid
        if uid <= 0:
            return jsonify({"error": "❌ UID không hợp lệ"}), 400

        tokens = load_tokens(server)
        target_success = 10000

        if not tokens:
            return jsonify({"error": f"❌ Không tìm thấy token hợp lệ cho server {server}"}), 500

        print(f"🚀 Sending visits to UID: {uid} | {len(tokens)} tokens | Server: {server}")

        # Tạo event loop mới, tránh conflict với Flask
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            total_success, total_sent, player_info = loop.run_until_complete(
                send_until_10000_success(tokens, uid, server, target_success=target_success)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)  # ← quan trọng: reset sau khi dùng xong

        if player_info:
            return jsonify({
                "fail": target_success - total_success,
                "level": player_info.get("level", 0),
                "likes": player_info.get("likes", 0),
                "nickname": player_info.get("nickname", ""),
                "region": player_info.get("region", ""),
                "success": total_success,
                "uid": player_info.get("uid", 0)
            }), 200
        else:
            return jsonify({
                "error": "❌ Không thể đọc thông tin player",
                "success": total_success,
                "fail": target_success - total_success
            }), 500

    except Exception as e:
        app.logger.error(f"❌ Route error: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5090, debug=False)
