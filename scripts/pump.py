import serial
import time

class SyringePump:
    """
    シリンジポンプを制御するためのクラス
    """
    def __init__(self, port, baudrate=9600, timeout=2):
        """
        シリンジポンプへの接続設定
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # シリアル通信オブジェクト

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
            # コマンドの末尾にCR+LFを付けて送信
            full_command = command + "\r\n"
            self.ser.write(full_command.encode('ascii'))
            # ポンプからの応答を待機
            time.sleep(0.5)
            response = self.ser.read_all().decode('ascii', errors="ignore").strip()
            return response
        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            return None

    def set_diameter(self, diameter_mm):
        """
        シリンジの直径を設定する（mm単位）。
        ※このコマンドが動作のために最も重要です。
        """
        # "DIA" の部分はポンプのマニュアルに合わせて変更してください
        command = f"DIA {diameter_mm}"
        response = self.send_command(command)
        print(f"Set diameter to {diameter_mm} mm: {response}")

    def set_rate(self, rate_value, rate_unit='MH'):
        """
        流量設定。単位も指定可能 (MH: mL/h, MM: mL/minなど)
        """
        command = f"RAT {rate_value} {rate_unit}"
        response = self.send_command(command)
        print(f"Set rate to {rate_value} {rate_unit}: {response}")

    def set_volume(self, volume_value, volume_unit='UL'):
        """
        体積設定。単位も指定可能 (UL: µL, ML: mLなど)
        """
        command = f"VOL {volume_value} {volume_unit}"
        response = self.send_command(command)
        print(f"Set volume to {volume_value} {volume_unit}: {response}")

    def set_direction(self, direction="INF"):
        """
        注入方向設定（INF: 押出, WDR: 吸引）
        """
        command = f"DIR {direction}" # ポンプによっては "DIRE" の場合もある
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
        """ ポンプをリセットする """
        command = "RST"
        response = self.send_command(command)
        print(f"Resetting pump: {response}")