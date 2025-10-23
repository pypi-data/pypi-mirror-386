import websocket
import os
import json
import zlib
import threading
from urllib.parse import urlparse

class KiponosClient:
    Q_BOOTSTRAP = "/user/queue/sdk-boot"  # Spring Boot user-specific queue
    VALUE = "value"  # Ѵ, 𝚟  𝑣, ѵ, 𝜈

    def __init__(self, server_url="wss://kiponos.io/api/io-kiponos-sdk", kiponos=None):
        self.server_url = server_url
        self.ws=None
        self.kiponos_id = os.environ.get("KIPONOS_ID")
        self.kiponos_access = os.environ.get("KIPONOS_ACCESS")
        if not self.kiponos_id or not self.kiponos_access:
            raise ValueError("Must provide env vars: KIPONOS_ID and KIPONOS_ACCESS")
        self.kiponos = kiponos
        self.config_tree = {}
        self.team_info = {}
        self.team_id = ""
        self.last_sub_id = 200
        self.handlers = {}  # Map sub_id --> handler
        self.listener_thread = None
        self.is_connected = False

    def _get_headers(self):
        headers = []
        headers.append(f"sdk-id-token: {self.kiponos_id}")
        headers.append(f"sdk-access-token: {self.kiponos_access}")
        headers.append(f"kiponos-id: {self.kiponos}")
        headers.append(f"sdk-version: 4.2.Esther")
        return headers

    # /topic/team
    def _subs_channel(self, channel_prefix, channel_name, handler):
        try:
            self.last_sub_id += 1
            dest = f"{channel_prefix}/{channel_name}"
            frame = f"SUBSCRIBE\nid:{self.last_sub_id}\ndestination:{dest}\n\n\0"
            self.handlers[str(self.last_sub_id)] = handler
            self.ws.send(frame)
            print(f"Subscribed {self.last_sub_id}: {dest}")
            return self
        except Exception as e:
            print(f"Error subscribe {channel_name}")

    def _subs_queue(self, queue_name):
        return self._subs_channel("/user/queue", queue_name)

    def _subs_topic(self, topic_name, handler):
        return self._subs_channel(f"/topic/team/{self.team_id}", topic_name, handler)

    def on_key_created(self, delta):
        if "key" in delta:
            self.config_tree[delta["key"]] = {self.VALUE: ""}
            print(f"Key Created: {delta['key']}")

        return self

    def on_val_updated(self, delta):
        if "key" in delta and "value" in delta:
            self.config_tree[delta["key"]] = {self.VALUE: delta["value"]}
            print(f"Value updated: {delta['key']} = {delta['value']}")

        return self

    def connect(self):
        """Establish Websocket Connection."""
        self.ws = websocket.WebSocket()
        headers = self._get_headers()

        try:
            self.ws.connect(self.server_url, header=headers)
            self.is_connected = True
        except Exception as e:
            self.is_connected = False
            print(f"Connection Error: {e}")
            raise

        # STOMP CONNECT
        host = urlparse(self.server_url).hostname
        connect_frame = f"CONNECT\naccept-version:1.2\nhost:{host}\n\n\0"
        self.ws.send(connect_frame)

        # Verify connect
        response = self.ws.recv()
        if not isinstance(response, str) or not response.startswith("CONNECTED"):
            self.is_connected = False
            raise ConnectionError(f"STOMP Connection Failed: {response}")

        # Subscribe Bootstrap
        sub_id = 0
        sub_frame = f"SUBSCRIBE\nid:{sub_id}\ndestination:{self.Q_BOOTSTRAP}\n\n\0"
        self.ws.send(sub_frame)

        # Receive Binary Zip Payload
        boot_msg = self.ws.recv()
        if not isinstance(boot_msg, bytes):
            raise ValueError(f"Expected Binary Message. Got: {type(boot_msg)}")

        # Parse STOMP boot message
        command, headers, body = self._parse_stomp_frame(boot_msg)
        if command != "MESSAGE":
            raise ValueError(f"Expected MESSAGE frame. Got: {command}")

        print(f"Got Binary Size: {len(body)} bytes")

        # Decompress zlib (simple zip)
        try:
            decompressed = zlib.decompress(body, wbits=-zlib.MAX_WBITS)
            json_arr_str = decompressed.decode("utf-8")
        except Exception as e:
            print(f"zlib Decompress failed: {e}")
            raise

        # JSON Array
        try:
            json_arr = json.loads(json_arr_str)
            print("Got JSONArray")
        except json.JSONDecodeError as e:
            print(f"JSON Parse Failed: {e}")
            raise

        # Config Tree and Team Info
        self.config_tree = json_arr[0] if len(json_arr) > 0 else {}
        self.team_info = json_arr[1] if len(json_arr) > 1 else {}
        self.team_id = self.team_info.get("teamId")

        if self.team_id is None:
            raise ValueError("No teamId - unable to subscribe to team topics.")

        print(f"Team Id: {self.team_id}")
        print(f"Config Keys: {list(self.config_tree.keys())}")

        self._subs_topic("config-key-created", self.on_key_created)
        self._subs_topic("config-val-updated", self.on_val_updated)

        self.listener_thread = threading.Thread(target=self._main_listener, daemon=True)
        self.listener_thread.start()

        return self

    def _parse_stomp_frame(self, data: bytes):
        header_end = data.find(b"\n\n")
        if header_end == -1:
            raise ValueError("No header end in STOMP frame")

        header_bytes = data[:header_end]
        body = data[header_end + 2 :]
        headers_str = header_bytes.decode("utf-8")
        lines = headers_str.split("\n")
        command = lines[0].strip()
        headers = {}
        for line in lines[1:]:
            if line.strip():
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()

        if body.endswith(b"\0"):
            body = body[:-1]

        if "content-length" in headers:
            length = int(headers["content-length"])
            if len(body) != length:
                raise ValueError(f"Expected Body Length: {length}. Got: {len(body)} ")

        return command, headers, body

    def _main_listener(self):
        while self.ws and self.is_connected:
            try:
                print(
                    f"---[  Main Listener  -  Listening  ]------[ is_connected: {self.is_connected}]"
                )

                msg = self.ws.recv()

                # print(f"MainListener - Got Msg: {msg}")
                if isinstance(msg, str) and msg.startswith("MESSAGE"):

                    header_end = msg.find("\n\n")
                    if header_end == -1:
                        print("No header in STOMP delta message")
                        continue

                    header_str = msg[:header_end]
                    body = msg[header_end + 2 :].rstrip("\0")
                    lines = header_str.split("\n")
                    command = lines[0].strip()
                    headers = {}
                    for line in lines[1:]:
                        if line.strip():
                            k, v = line.split(":", 1)
                            headers[k.strip()] = v.strip()

                    if command == "MESSAGE":
                        sub_id = headers.get("subscription")
                        if sub_id in self.handlers:
                            try:
                                delta = json.loads(body)
                                print(f"Handling {sub_id}: {delta}")
                                self.handlers[sub_id](delta)
                            except json.JSONDecodeError as e:
                                print(f"Error parsing delta: {e}")
                        else:
                            print(f"No Handler for sub_id: {sub_id}")
                    else:
                        print(f"Unexpected command: {command}")
            except websocket.WebSocketConnectionClosedException as e:
                print(f"Main Listener Error: Socket Closed: {e}")
                self.is_connected = False
                self.close()
                break
            except Exception as e:
                print(f"Main Listener Error: {e}")
                self.is_connected = False
                self.close()
                break

            #         command, headers, body = self._parse_stomp_frame(msg)
            #         if command == "MESSAGE":
            #             sub_id = headers.get("subscription")
            #             if sub_id in self.handlers:
            #                 try:
            #                     body_str = body.decode("utf-8")
            #                     delta = json.loads(body_str)
            #                     print(f"Handling SubId: {sub_id} Got Delta: {delta}")
            #                     self.handlers[sub_id](delta)
            #                 except json.JSONDecodeError as e:
            #                     print(f"Error parsing delta: {e}")
            # except Exception as e:
            #     print(f"Main Listener Error: {e}")
            #     break

    def send(self, message):
        """Send Message to Kiponos Server."""
        if self.ws and self.is_connected:
            try:
                self.ws.send(message)
            except websocket.WebSocketConnectionClosedException:
                print("Unable to send; Socket closed")
                self.is_connected = False
                self.close()

    def get(self, key_name, default=None):
        node = self.config_tree.get(key_name, {})
        return node.get(self.VALUE, default) if isinstance(node, dict) else default
        # return self.config_tree.get(key_name, default)[self.VALUE]

    def close(self):
        """Close the Connection."""
        if self.ws and self.is_connected:
            try:
                self.ws.send("DISCONNECT\n\n\0")
            except websocket.WebSocketConnectionClosedException:
                pass

            self.ws.close()
            self.is_connected = False

        if self.listener_thread:
            self.listener_thread.join(timeout=5)
