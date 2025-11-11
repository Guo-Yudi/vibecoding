import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Host = "rtasr.xfyun.cn"
        self.HttpProto = "HTTP/1.1"
        self.RequestUri = "/v1/ws"
        self.Algorithm = "hmac-sha256"
        self.Headers = ["host", "date", "request-line"]
        self.Url = f"wss://{self.Host}{self.RequestUri}"

    def create_url(self):
        date = format_date_time(mktime(datetime.now().timetuple()))
        signature_origin = f"host: {self.Host}\ndate: {date}\nGET {self.RequestUri} {self.HttpProto}"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.APIKey}", algorithm="{self.Algorithm}", headers="{" ".join(self.Headers)}", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.Host
        }
        url = self.Url + '?' + urlencode(v)
        return url

def run_asr(audio_stream, app_id, api_key, api_secret, client_ws):
    final_result = ""
    sentence_buffer = {}

    def on_message(ws, message):
        nonlocal final_result, sentence_buffer
        try:
            msg = json.loads(message)
            code = msg.get('code')
            sid = msg.get('sid')
            if code != 0:
                errMsg = msg.get('message')
                print(f"sid:{sid} error:{errMsg} code is:{code}")
                if not client_ws.closed:
                    client_ws.send(json.dumps({"error": f"ASR Error: {errMsg}"}))
                return

            data = msg.get('data')
            if data:
                if data['action'] == 'result':
                    res = data['data']['cn']['st']
                    is_final = res['type'] == '1'
                    
                    current_sentence = ""
                    for part in res['rt']:
                        for word_info in part['ws']:
                            word = word_info['cw'][0]['w']
                            sentence_buffer[part['sn']] = sentence_buffer.get(part['sn'], "") + word
                    
                    # 组合所有句子的当前结果
                    full_text = "".join([sentence_buffer[k] for k in sorted(sentence_buffer.keys())])

                    if not client_ws.closed:
                        client_ws.send(json.dumps({"intermediate_result": full_text}))

                    if is_final:
                        final_result = full_text

                elif data['action'] == 'error':
                    print(f"ASR Error: {data}")
                    if not client_ws.closed:
                        client_ws.send(json.dumps({"error": f"ASR Error: {data}"}))

        except Exception as e:
            print(f"Receive msg, but parse exception: {e}")

    def on_error(ws, error):
        print("### ASR error ###", error)
        if not client_ws.closed:
            client_ws.send(json.dumps({"error": "ASR service connection error."}))

    def on_close(ws, close_status_code, close_msg):
        print("### ASR closed ###")

    def on_open(ws):
        def run(*args):
            d = {
                "common": {"app_id": app_id},
                "business": {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "sample_rate": "16000", "aue": "raw"},
                "data": {"status": 0, "format": "audio/L16;rate=16000", "encoding": "raw", "audio": ""}
            }
            ws.send(json.dumps(d))

            for chunk in audio_stream:
                if not chunk:
                    break
                ws.send(chunk, websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)

            ws.send(json.dumps({"data": {"status": 2}}))
            print("send end tag success")
        thread.start_new_thread(run, ())

    wsParam = Ws_Param(APPID=app_id, APIKey=api_key, APISecret=api_secret)
    wsUrl = wsParam.create_url()
    
    ws_app = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws_app.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    
    return final_result