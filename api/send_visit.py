import json
import random
import time
import httpx
from concurrent.futures import ThreadPoolExecutor

last_sent_cache = {}

def Encrypt_ID(x):
    x = int(x)
    dec = ['80','81','82','83','84','85','86','87','88','89','8a','8b','8c','8d','8e','8f','90','91','92','93','94','95','96','97','98','99','9a','9b','9c','9d','9e','9f','a0','a1','a2','a3','a4','a5','a6','a7','a8','a9','aa','ab','ac','ad','ae','af','b0','b1','b2','b3','b4','b5','b6','b7','b8','b9','ba','bb','bc','bd','be','bf','c0','c1','c2','c3','c4','c5','c6','c7','c8','c9','ca','cb','cc','cd','ce','cf','d0','d1','d2','d3','d4','d5','d6','d7','d8','d9','da','db','dc','dd','de','df','e0','e1','e2','e3','e4','e5','e6','e7','e8','e9','ea','eb','ec','ed','ee','ef','f0','f1','f2','f3','f4','f5','f6','f7','f8','f9','fa','fb','fc','fd','fe','ff']
    xxx = ['1','01','02','03','04','05','06','07','08','09','0a','0b','0c','0d','0e','0f','10','11','12','13','14','15','16','17','18','19','1a','1b','1c','1d','1e','1f','20','21','22','23','24','25','26','27','28','29','2a','2b','2c','2d','2e','2f','30','31','32','33','34','35','36','37','38','39','3a','3b','3c','3d','3e','3f','40','41','42','43','44','45','46','47','48','49','4a','4b','4c','4d','4e','4f','50','51','52','53','54','55','56','57','58','59','5a','5b','5c','5d','5e','5f','60','61','62','63','64','65','66','67','68','69','6a','6b','6c','6d','6e','6f','70','71','72','73','74','75','76','77','78','79','7a','7b','7c','7d','7e','7f']
    x = x / 128
    if x > 128:
        x = x / 128
        if x > 128:
            x = x / 128
            if x > 128:
                x = x / 128
                strx = int(x)
                y = (x - int(strx)) * 128
                z = (y - int(y)) * 128
                n = (z - int(z)) * 128
                m = (n - int(n)) * 128
                return dec[int(m)] + dec[int(n)] + dec[int(z)] + dec[int(y)] + xxx[int(x)]
            else:
                strx = int(x)
                y = (x - int(strx)) * 128
                z = (y - int(y)) * 128
                n = (z - int(z)) * 128
                return dec[int(n)] + dec[int(z)] + dec[int(y)] + xxx[int(x)]
    # لو كانت قيمه x أقل أو غير مطابقه لشرط السابق، ترجع None
    return None

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

def encrypt_api(plain_text):
    plain_text = bytes.fromhex(plain_text)
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

def send_visit_request(token, TARGET):
    url = "https://clientbp.common.ggbluefox.com/GetPlayerPersonalShow"
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)',
        'Connection': 'Keep-Alive',
        'Expect': '100-continue',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': 'OB50',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {token}'
    }
    try:
        resp = httpx.post(url, headers=headers, data=TARGET, verify=False, timeout=10)
        if resp.status_code == 200:
            return {"token": token[:20] + "...", "status": "success"}
        else:
            return {"token": token[:20] + "...", "status": f"failed ({resp.status_code})"}
    except httpx.RequestError as e:
        return {"token": token[:20] + "...", "status": f"error ({e})"}

def handler(event, context):
    # event يحتوي على keys: "method", "query", "body" حسب الطلب
    # جلب player_id من query string
    query = event.get("query", {})
    player_id = query.get("player_id")

    if not player_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "player_id is required"})
        }

    try:
        player_id_int = int(player_id)
    except ValueError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "player_id must be an integer"})
        }

    now = time.time()
    last_sent = last_sent_cache.get(player_id_int, 0)
    seconds_since_last = now - last_sent

    if seconds_since_last < 86400:  # 24 ساعة
        remaining = int(86400 - seconds_since_last)
        return {
            "statusCode": 429,
            "body": json.dumps({
                "error": "Visits already sent within last 24 hours",
                "seconds_until_next_allowed": remaining
            })
        }

    # جلب التوكنات من API خارجي
    try:
        token_data = httpx.get("https://auto-token-bngx.onrender.com/api/get_jwt", timeout=10).json()
        tokens = token_data.get("tokens", [])
        if not tokens:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "No tokens found"})
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to fetch tokens: {e}"})
        }

    tokens = random.sample(tokens, min(200, len(tokens)))

    encrypted_id = Encrypt_ID(player_id_int)
    if not encrypted_id:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Encryption failed"})
        }

    encrypted_api_data = encrypt_api(f"08{encrypted_id}1007")
    TARGET = bytes.fromhex(encrypted_api_data)

    results = []
    failed_tokens = set()

    def worker(token):
        if token in failed_tokens:
            return None

        res = send_visit_request(token, TARGET)

        if "failed" in res["status"] or "error" in res["status"]:
            failed_tokens.add(token)
            return None
        return res

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=40) as executor:
        futures = [executor.submit(worker, token) for token in tokens]

        for future in futures:
            result = future.result()
            if result:
                results.append(result)

    visits_sent = len(results)
    last_sent_cache[player_id_int] = now

    return {
        "statusCode": 200,
        "body": json.dumps({
            "player_id": player_id_int,
            "visits_added": visits_sent,
            "seconds_until_next_allowed": 86400,
            "details": results
        })
    }
