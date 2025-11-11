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
import gevent

# 讯飞实时语音转写服务的认证参数生成类
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
        """生成带鉴权参数的WebSocket URL"""
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

# 实时语音转写客户端
class ASRClient:
    def __init__(self, app_id, api_key, api_secret, audio_stream, client_ws):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.audio_stream = audio_stream
        self.client_ws = client_ws  # 前端WebSocket连接

        self.final_result = ""
        self.sentence_buffer = {}
        self.ws_app = None
        self.ws_open = False

    def on_message(self, ws, message):
        """处理从讯飞服务器收到的消息"""
        try:
            msg = json.loads(message)
            code = msg.get('code')
            sid = msg.get('sid')
            if code != 0:
                errMsg = msg.get('message')
                self.send_to_client({"error": f"ASR Error: {errMsg} (sid: {sid})"})
                return

            data = msg.get('data')
            if data:
                if data['action'] == 'result':
                    res = data['data']['cn']['st']
                    is_final = res['type'] == '1'
                    
                    # 实时拼接句子
                    for part in res['rt']:
                        for word_info in part['ws']:
                            word = word_info['cw'][0]['w']
                            self.sentence_buffer[part['sn']] = self.sentence_buffer.get(part['sn'], "") + word
                    
                    full_text = "".join([self.sentence_buffer[k] for k in sorted(self.sentence_buffer.keys())])
                    
                    # 发送中间结果到前端
                    self.send_to_client({"intermediate_result": full_text})

                    if is_final:
                        self.final_result = full_text
                        # 如果需要，可以在这里处理最终结果的逻辑
                        
                elif data['action'] == 'error':
                    self.send_to_client({"error": f"ASR Action Error: {data}"})

        except Exception as e:
            print(f"ASR on_message exception: {e}")
            self.send_to_client({"error": "ASR message parsing error."})

    def on_error(self, ws, error):
        """处理WebSocket错误"""
        print(f"### ASR WebSocket Error ###: {error}")
        self.send_to_client({"error": "ASR service connection error."})
        self.ws_open = False

    def on_close(self, ws, close_status_code, close_msg):
        """处理WebSocket关闭事件"""
        print(f"### ASR WebSocket Closed ### Code: {close_status_code}, Msg: {close_msg}")
        self.ws_open = False
        # 可以在这里通知前端连接已关闭
        self.send_to_client({"status": "asr_closed"})


    def on_open(self, ws):
        """WebSocket连接建立后，启动音频发送协程"""
        print("### ASR WebSocket Opened ###")
        self.ws_open = True
        gevent.spawn(self.send_audio_thread)

    def send_audio_thread(self):
        """在单独的协程中发送音频数据"""
        # 发送业务参数
        business_params = {
            "common": {"app_id": self.app_id},
            "business": {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "sample_rate": "16000", "aue": "raw"},
            "data": {"status": 0, "format": "audio/L16;rate=16000", "encoding": "raw", "audio": ""}
        }
        self.ws_app.send(json.dumps(business_params))

        # 持续发送音频流
        for chunk in self.audio_stream:
            if not self.ws_open:
                print("ASR connection closed, stopping audio send.")
                break
            if not chunk:
                break
            self.ws_app.send(chunk, websocket.ABNF.OPCODE_BINARY)
            gevent.sleep(0.04)  # 控制发送速率

        # 发送结束帧
        if self.ws_open:
            end_frame = {"data": {"status": 2}}
            self.ws_app.send(json.dumps(end_frame))
            print("### Sent ASR end tag ###")

    def send_to_client(self, data):
        """安全地向前端发送数据"""
        try:
            if not self.client_ws.closed:
                self.client_ws.send(json.dumps(data))
        except Exception as e:
            print(f"Failed to send to client: {e}")

    def run(self):
        """启动ASR客户端"""
        wsParam = Ws_Param(APPID=self.app_id, APIKey=self.api_key, APISecret=self.api_secret)
        wsUrl = wsParam.create_url()
        
        self.ws_app = websocket.WebSocketApp(
            wsUrl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # run_forever会阻塞，直到连接关闭
        self.ws_app.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        # 返回最终识别结果
        return self.final_result

# 主入口函数，供app.py调用
def run_asr(app_id, api_key, api_secret, audio_stream, client_ws):
    asr_client = ASRClient(app_id, api_key, api_secret, audio_stream, client_ws)
    return asr_client.run()