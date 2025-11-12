import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlencode
import gevent
from gevent import Greenlet
from websocket import create_connection, WebSocketException

class ASRClient(Greenlet):
    def __init__(self, app_id, api_key, api_secret, audio_queue, client_ws):
        super().__init__()
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.audio_queue = audio_queue
        self.client_ws = client_ws

        self.host = "iat-api.xfyun.cn"
        self.request_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.ws = None
        self.is_connected = False
        self.full_transcript = ""

    def _generate_auth_url(self):
        """
        Generates the authentication URL according to the iFlyTek documentation.
        """
        # 1. Generate date in RFC1123 format
        date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

        # 2. Create the signature string
        tmp_signature_origin = f"host: {self.host}\ndate: {date}\nGET /v2/iat HTTP/1.1"
        
        # 3. HMAC-SHA256 signing
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), tmp_signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')

        # 4. Create the authorization string
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

        # 5. Build the final URL
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.request_url + '?' + urlencode(v)
        return url

    def connect(self):
        """Establish WebSocket connection."""
        try:
            auth_url = self._generate_auth_url()
            print(f"Connecting to: {auth_url}")
            self.ws = create_connection(auth_url, timeout=10)
            self.is_connected = True
            print("Connection successful, ready to send audio.")
            return True
        except WebSocketException as e:
            print(f"Connection failed: WebSocket error: {e}")
            return False
        except Exception as e:
            print(f"Connection failed: Other error: {e}")
            return False

    def _recv_msg(self):
        """Receive and process messages from the ASR server."""
        while self.is_connected:
            try:
                msg_str = self.ws.recv()
                if not msg_str:
                    break
                
                msg = json.loads(msg_str)
                code = msg.get('code')
                if code != 0:
                    errMsg = msg.get('message', 'Unknown error')
                    print(f"ASR server error: {code} - {errMsg}")
                    self.send_to_client(json.dumps({"error": f"ASR Error: {errMsg}"}))
                    break

                data = msg.get('data', {})
                result = data.get('result', {})
                status = data.get('status')
                
                current_text = ""
                if result:
                    ws = result.get('ws', [])
                    for i in ws:
                        for w in i.get('cw', []):
                            current_text += w.get('w', '')

                if status != 2:
                    # Intermediate result. This is always the full text so far.
                    self.full_transcript = current_text
                    if self.full_transcript:
                        print(f"实时结果: {self.full_transcript}")
                        self.send_to_client(json.dumps({"intermediate_result": self.full_transcript}))
                else: # Final result
                    # If the final message is just punctuation, append it to the transcript we've built so far.
                    is_just_punctuation = len(current_text) > 0 and all(c in '。，？！.,?!' for c in current_text)
                    
                    if is_just_punctuation and self.full_transcript:
                        self.full_transcript += current_text
                    # If the final message has actual text, it's a final correction and should be trusted as the complete result.
                    elif current_text:
                        self.full_transcript = current_text
                    # If the final message is empty, we just stick with what we have.

                    print(f"ASR session finished. Final result: {self.full_transcript}")
                    self.send_to_client(json.dumps({"final_text": self.full_transcript}))
                    break

            except WebSocketException as e:
                print(f"Receiving error: Connection interrupted: {e}")
                break
            except Exception as e:
                print(f"Receiving error: Unknown error: {e}")
                break
        self.close()

    def send_to_client(self, message):
        """Send message to the web client."""
        try:
            if self.client_ws:
                self.client_ws.send(message)
        except Exception as e:
            print(f"Failed to send to client: {e}")

    def _send_audio(self):
        """Send audio data from the queue to the ASR server."""
        # 1. Send business parameters frame
        business_params = {
            "common": {"app_id": self.app_id},
            "business": {
                "language": "zh_cn",
                "domain": "iat",
                "accent": "mandarin",
                "dwa": "wpgs" # For punctuation
            },
            "data": {
                "status": 0,
                "format": "audio/L16;rate=16000",
                "encoding": "raw",
                "audio": ""
            }
        }
        try:
            self.ws.send(json.dumps(business_params))
        except WebSocketException as e:
            print(f"Failed to send business params: {e}")
            self.close()
            return

        # 2. Send audio frames
        while self.is_connected:
            try:
                chunk = self.audio_queue.get(timeout=5)
                if chunk is None:  # End of stream signal
                    break
                
                # Base64 encode the audio chunk
                audio_b64 = base64.b64encode(chunk).decode('utf-8')
                
                audio_frame = {
                    "data": {
                        "status": 1,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": audio_b64
                    }
                }
                self.ws.send(json.dumps(audio_frame))
                gevent.sleep(0.04) # Simulate 40ms interval

            except gevent.queue.Empty:
                # Timeout waiting for audio, can happen if user pauses
                print("Audio queue empty, continuing to wait...")
                continue
            except WebSocketException as e:
                print(f"Audio sending error: WebSocket connection lost: {e}")
                break
            except Exception as e:
                print(f"Audio sending loop error: {e}")
                break

        # 3. Send end frame
        try:
            end_frame = {
                "data": {
                    "status": 2,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": ""
                }
            }
            self.ws.send(json.dumps(end_frame))
            print("Sent end-of-stream frame to ASR server.")
        except WebSocketException as e:
            print(f"Failed to send end frame: {e}")
        finally:
            print("Audio sending greenlet finished.")

    def _run(self):
        """Main greenlet execution: connect and manage I/O greenlets."""
        if self.connect():
            sender = Greenlet(self._send_audio)
            receiver = Greenlet(self._recv_msg)
            
            sender.start()
            receiver.start()
            
            gevent.joinall([sender, receiver])
        
        self.close()
        print("ASR client greenlet has stopped.")
        
    def close(self):
        """Safely close the WebSocket connections."""
        if self.is_connected and self.ws:
            self.is_connected = False
            try:
                if self.ws.connected:
                    self.ws.close(status=1000, reason="Client closing")
                print("ASR WebSocket connection closed.")
            except Exception as e:
                print(f"Error while closing ASR connection: {e}")
        
        if self.client_ws:
            try:
                self.client_ws.close(1000, "ASR service finished")
                print("Client WebSocket connection closed.")
            except Exception as e:
                print(f"Error while closing client connection: {e}")