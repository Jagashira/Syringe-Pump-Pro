import inquirer
import time
from typing import Any, Dict

# pump.py から SyringePump クラスをインポート
from pump import SyringePump

PUMP_PORT = "COM3" # 例: 'COM3', '/dev/ttyUSB0' など

# --- 共通関数 ---

def is_positive_float(answers: Dict[str, Any], current: str) -> bool:
    """入力が正の小数であることを検証するバリデータ"""
    if not current:
        return False
    return current.replace('.', '', 1).isdigit() and float(current) > 0

def calculate_wait_time(volume_uL: float, rate_mlh: float) -> float:
    """注入完了までの時間を計算する（秒単位）"""
    if rate_mlh <= 0:
        return 0
    # 時間(h) = (体積(µL) / 1000) / 流量(mL/h)
    # 時間(s) = 時間(h) * 3600
    # 念のため少しだけ待機時間を追加する
    wait_seconds = (volume_uL / 1000 / rate_mlh) * 3600
    return wait_seconds + 1.0 # 1秒のバッファ

def get_single_parameters():
    """`single` の場合のパラメータ入力"""
    questions = [
        inquirer.Text(
            'volume',
            message='Enter the droplet volume (µL):',
            default='1.0',
            validate=is_positive_float
        ),
        inquirer.Text(
            'rate',
            message='Enter the flow rate (mL/h):',
            default='0.5',
            validate=is_positive_float
        )
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        exit("Operation cancelled by user.")
    return float(answers['volume']), float(answers['rate'])

def get_coalescence_parameters():
    """`coalescence` の場合のパラメータ入力"""
    questions = [
        inquirer.Text('leading_volume', message='Enter the leading droplet volume (µL):', default='7.0', validate=is_positive_float),
        inquirer.Text('leading_rate', message='Enter the leading droplet flow rate (mL/h):', default='0.5', validate=is_positive_float),
        inquirer.Text('trailing_volume', message='Enter the trailing droplet volume (µL):', default='2.0', validate=is_positive_float),
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
    pump = SyringePump(port=PUMP_PORT)

    try:
        pump.connect()
        if pump.ser is None:
            print("Failed to connect to the pump. Please check the port and connection.")
            return

        # 最初に `single` か `coalescence` を選ばせる
        questions = [
            inquirer.List(
                'experiment_type',
                message='What type of experiment would you like to run?',
                choices=['single', 'coalescence']
            )
        ]
        answers = inquirer.prompt(questions)

        if not answers:
            print("No experiment type selected. Exiting.")
            return
        
        # デフォルトの注入方向を設定
        pump.set_direction("INF")

        if answers['experiment_type'] == 'single':
            volume, rate = get_single_parameters()
            print("-" * 20)
            print(f"Running single droplet experiment...")
            
            # ポンプにパラメータを設定して実行
            pump.set_volume(volume)
            pump.set_rate(rate)
            pump.run()
            
            # 注入完了まで待機
            wait_time = calculate_wait_time(volume, rate)
            print(f"Waiting for {wait_time:.2f} seconds for the infusion to complete.")
            time.sleep(wait_time)
            pump.stop()
            print("Single experiment finished.")

        elif answers['experiment_type'] == 'coalescence':
            l_vol, l_rate, t_vol, t_rate = get_coalescence_parameters()
            print("-" * 20)
            print(f"Running coalescence experiment...")

            # 1. 先行液滴の注入
            print("\n[Step 1/2] Infusing leading droplet...")
            pump.set_volume(l_vol)
            pump.set_rate(l_rate)
            pump.run()
            
            wait_time_1 = calculate_wait_time(l_vol, l_rate)
            print(f"Waiting for {wait_time_1:.2f} seconds...")
            time.sleep(wait_time_1)
            pump.stop()
            print("Leading droplet infusion finished.")

            # 2. 後続液滴の注入
            print("\n[Step 2/2] Infusing trailing droplet...")
            pump.set_volume(t_vol)
            pump.set_rate(t_rate)
            pump.run()
            
            wait_time_2 = calculate_wait_time(t_vol, t_rate)
            print(f"Waiting for {wait_time_2:.2f} seconds...")
            time.sleep(wait_time_2)
            pump.stop()
            print("Trailing droplet infusion finished.")
            
            print("\nCoalescence experiment finished.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # スクリプト終了時に必ずポンプから切断する
        print("-" * 20)
        pump.disconnect()

if __name__ == "__main__":
    main()