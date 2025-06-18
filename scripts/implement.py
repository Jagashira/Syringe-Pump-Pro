import inquirer
import time
import argparse
from typing import Any, Dict

# pump.py から SyringePump クラスをインポート
from pump import SyringePump

# --- 共通関数 ---

def is_positive_float(answers: Dict[str, Any], current: str) -> bool:
    """入力が正の小数であることを検証するバリデータ"""
    if not current:
        return False
    try:
        return float(current) > 0
    except ValueError:
        return False

def calculate_wait_time(volume_uL: float, rate_mlh: float) -> float:
    """注入完了までの時間を計算する（秒単位）"""
    if rate_mlh <= 0:
        return 0
    # 時間(h) = (体積(µL) / 1000) / 流量(mL/h)
    # 時間(s) = 時間(h) * 3600
    wait_seconds = (volume_uL / 1000 / rate_mlh) * 3600
    # 注入完了後、少し余裕を持たせる
    return wait_seconds + 1.0

def get_single_parameters():
    """`single` の場合のパラメータ入力"""
    questions = [
        inquirer.Text('volume', message='Enter the droplet volume (uL):', default='1.0', validate=is_positive_float),
        inquirer.Text('rate', message='Enter the flow rate (mL/h):', default='0.5', validate=is_positive_float)
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        exit("Operation cancelled by user.")
    return float(answers['volume']), float(answers['rate'])

def get_coalescence_parameters():
    """`coalescence` の場合のパラメータ入力"""
    questions = [
        inquirer.Text('leading_volume', message='Enter the leading droplet volume (uL):', default='7.0', validate=is_positive_float),
        inquirer.Text('leading_rate', message='Enter the leading droplet flow rate (mL/h):', default='0.5', validate=is_positive_float),
        inquirer.Text('trailing_volume', message='Enter the trailing droplet volume (uL):', default='2.0', validate=is_positive_float),
        inquirer.Text('trailing_rate', message='Enter the trailing droplet flow rate (mL/h):', default='0.5', validate=is_positive_float)
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        exit("Operation cancelled by user.")
    return (
        float(answers['leading_volume']), float(answers['leading_rate']),
        float(answers['trailing_volume']), float(answers['trailing_rate'])
    )

def main():
    """メイン実行関数"""
    # --- コマンドライン引数の設定 ---
    parser = argparse.ArgumentParser(description="Control the syringe pump for experiments.")
    parser.add_argument("--port", type=str, required=True, help="Serial port for the pump (e.g., COM3, /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=19200, help="Baud rate for the serial connection (default: 19200)")
    parser.add_argument("--dia", type=float, required=True, help="Diameter of the syringe in mm (e.g., 14.5 for a 10mL syringe)")
    args = parser.parse_args()

    # --- 引数を使ってポンプを初期化 ---
    pump = SyringePump(port=args.port, baudrate=args.baud)

    try:
        pump.connect()
        if pump.ser is None:
            return

        # --- 最も重要な初期設定 ---
        print("\n--- Initializing Pump ---")
        pump.reset()              # 1. ポンプをリセット
        pump.set_diameter(args.dia) # 2. シリンジの直径を設定 (最重要)
        pump.set_direction("INF") # 3. 注入方向を設定
        print("-------------------------\n")

        # 実験タイプの選択
        questions = [
            inquirer.List('experiment_type', message='What type of experiment would you like to run?', choices=['single', 'coalescence'])
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            print("No experiment type selected. Exiting.")
            return
        
        # --- 実験の実行 ---
        if answers['experiment_type'] == 'single':
            volume, rate = get_single_parameters()
            print("-" * 20)
            print(f"Running single droplet experiment...")
            pump.set_volume(volume, 'UL')
            pump.set_rate(rate, 'MH')
            pump.run()
            wait_time = calculate_wait_time(volume, rate)
            print(f"Waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            pump.stop()
            print("Single experiment finished.")

        elif answers['experiment_type'] == 'coalescence':
            l_vol, l_rate, t_vol, t_rate = get_coalescence_parameters()
            print("-" * 20)
            print(f"Running coalescence experiment...")

            # 1. 先行液滴
            print("\n[Step 1/2] Infusing leading droplet...")
            pump.set_volume(l_vol, 'UL')
            pump.set_rate(l_rate, 'MH')
            pump.run()
            wait_time_1 = calculate_wait_time(l_vol, l_rate)
            print(f"Waiting for {wait_time_1:.2f} seconds...")
            time.sleep(wait_time_1)
            pump.stop()
            print("Leading droplet infusion finished.")

            # 2. 後続液滴
            print("\n[Step 2/2] Infusing trailing droplet...")
            pump.set_volume(t_vol, 'UL')
            pump.set_rate(t_rate, 'MH')
            pump.run()
            wait_time_2 = calculate_wait_time(t_vol, t_rate)
            print(f"Waiting for {wait_time_2:.2f} seconds...")
            time.sleep(wait_time_2)
            pump.stop()
            print("Trailing droplet infusion finished.")
            
            print("\nCoalescence experiment finished.")

    except (KeyboardInterrupt):
        print("\nOperation cancelled by user. Stopping pump...")
        pump.stop()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("-" * 20)
        pump.disconnect()

if __name__ == "__main__":
    main()
