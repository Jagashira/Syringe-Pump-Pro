import serial
import time

class SyringePump:
    def __init__(self, port, baudrate=9600, timeout=2, default_rate_mlh=0.5, default_volume_uL=5.0, default_direction="INF"):
        """
        シリンジポンプへの接続設定
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # シリアル通信オブジェクト

        # デフォルトパラメータ
        self.default_rate_mlh = default_rate_mlh   # デフォルト流量（mL/h）
        self.default_volume_uL = default_volume_uL  # デフォルト体積（µL）
        self.default_direction = default_direction  # デフォルト注入方向（INF: 押し出し）

        # ユーザー設定
        self.rate_mlh = None
        self.volume_uL = None
        self.direction = None

    def connect(self):
        """ シリンジポンプに接続する """
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Connected to syringe pump on {self.port} with baudrate {self.baudrate}")
        except Exception as e:
            print(f"Error connecting to pump: {e}")
            self.ser = None

    def disconnect(self):
        """ シリンジポンプから切断する """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Disconnected from {self.port}")

    def send_command(self, command):
        """ シリンジポンプにコマンドを送信し、応答を取得する """
        if self.ser is None or not self.ser.is_open:
            print("Pump not connected!")
            return None
        try:
            self.ser.write((command + "\r\n").encode())  # コマンド送信（CRLF）
            time.sleep(0.5)  # 応答を待機
            response = self.ser.read_all().decode(errors="ignore")
            return response
        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            return None

    def set_rate(self, rate_mlh=None):
        """ 流量設定（mL/h）。設定されていない場合はデフォルト値を使用 """
        rate_mlh = rate_mlh if rate_mlh is not None else self.default_rate_mlh
        self.rate_mlh = rate_mlh  # ユーザーが設定した値を保持
        command = f"RAT {rate_mlh} MH"
        response = self.send_command(command)
        print(f"Set rate to {rate_mlh} mL/h: {response}")

    def set_volume(self, volume_uL=None):
        """ 体積設定（µL）。設定されていない場合はデフォルト値を使用 """
        volume_uL = volume_uL if volume_uL is not None else self.default_volume_uL
        self.volume_uL = volume_uL  # ユーザーが設定した値を保持
        command = f"VOL {volume_uL} uL"
        response = self.send_command(command)
        print(f"Set volume to {volume_uL} µL: {response}")

    def set_direction(self, direction=None):
        """ 注入方向設定（INF: 押出, WDR: 吸引）。設定されていない場合はデフォルト値を使用 """
        direction = direction if direction is not None else self.default_direction
        self.direction = direction  # ユーザーが設定した値を保持
        command = f"DIRE {direction}"
        response = self.send_command(command)
        print(f"Set direction to {direction}: {response}")

    def run(self):
        """ ポンプを開始 """
        command = "RUN"
        response = self.send_command(command)
        print(f"Running pump: {response}")

    def stop(self):
        """ ポンプを停止 """
        command = "STP"
        response = self.send_command(command)
        print(f"Stopping pump: {response}")

    def reset(self):
        """ ポンプをリセット（エラーチェック後） """
        command = "RST"
        response = self.send_command(command)
        print(f"Resetting pump: {response}")
