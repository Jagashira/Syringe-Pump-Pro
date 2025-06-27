import time
import argparse

# pump.py から SyringePump クラスをインポート
# Import the SyringePump class from pump.py
from pump import SyringePump

def calculate_wait_time(volume_uL: float, rate_mlh: float) -> float:
    """
    吸引完了までの時間を計算する（秒単位）
    Calculate the time required for aspiration to complete (in seconds).
    """
    if rate_mlh <= 0:
        return 0
    # 時間(h) = (体積(µL) / 1000) / 流量(mL/h)
    # Time (h) = (Volume (µL) / 1000) / Flow Rate (mL/h)
    # 時間(s) = 時間(h) * 3600
    # Time (s) = Time (h) * 3600
    wait_seconds = (volume_uL / 1000 / rate_mlh) * 3600
    # 吸引完了後、少し余裕を持たせる
    # Add a small buffer after aspiration is complete
    return wait_seconds + 1.0

def main():
    """メイン実行関数 (Main execution function)"""
    # --- コマンドライン引数の設定 (Command-line argument setup) ---
    parser = argparse.ArgumentParser(description="Aspirate a specific volume using the syringe pump.")
    parser.add_argument("--port", type=str, required=True, help="Serial port for the pump (e.g., COM3, /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=19200, help="Baud rate for the serial connection (default: 19200)")
    parser.add_argument("--dia", type=float, required=True, help="Diameter of the syringe in mm (e.g., 14.5 for a 10mL syringe)")
    args = parser.parse_args()

    # --- 吸引パラメータ (Aspiration Parameters) ---
    TARGET_VOLUME_UL = 500.0  # 吸引する体積 (µL) - Volume to aspirate
    ASPIRATION_RATE_MLH = 10.0 # 吸引する流量 (mL/h) - Aspiration flow rate

    # --- ポンプを初期化 (Initialize the pump) ---
    pump = SyringePump(port=args.port, baudrate=args.baud)

    try:
        pump.connect()
        if pump.ser is None:
            # 接続に失敗した場合は終了
            # Exit if connection fails
            return

        # --- ポンプの初期設定 (Initial Pump Setup) ---
        print("\n--- Initializing Pump for Aspiration ---")
        pump.reset()              # 1. ポンプをリセット (Reset the pump)
        pump.set_diameter(args.dia) # 2. シリンジの直径を設定 (Set syringe diameter) - VERY IMPORTANT
        pump.set_direction("WDR") # 3. 方向を吸引に設定 (Set direction to Withdraw) - KEY CHANGE
        print("----------------------------------------\n")

        # --- 吸引の実行 (Execute Aspiration) ---
        print(f"Preparing to aspirate {TARGET_VOLUME_UL} uL at {ASPIRATION_RATE_MLH} mL/h...")
        
        # 流量と体積を設定
        # Set the rate and volume
        pump.set_rate(ASPIRATION_RATE_MLH, 'MH')
        pump.set_volume(TARGET_VOLUME_UL, 'UL')
        
        # ポンプ作動
        # Run the pump
        pump.run()
        
        # 完了まで待機
        # Wait for completion
        wait_time = calculate_wait_time(TARGET_VOLUME_UL, ASPIRATION_RATE_MLH)
        print(f"Aspirating... waiting for {wait_time:.2f} seconds.")
        time.sleep(wait_time)
        
        # ポンプ停止
        # Stop the pump
        pump.stop()
        print(f"\nAspiration of {TARGET_VOLUME_UL} uL finished.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Stopping pump...")
        pump.stop()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # エラーが発生した場合でもポンプを停止しようと試みる
        # Attempt to stop the pump even if an error occurs
        if pump and pump.ser:
            pump.stop()
    finally:
        print("-" * 20)
        # 正常終了・異常終了問わず、必ず切断処理を行う
        # Always perform disconnection, regardless of normal or abnormal termination
        pump.disconnect()

if __name__ == "__main__":
    main()
