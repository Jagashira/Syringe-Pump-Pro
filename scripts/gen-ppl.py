import yaml
import os
import shutil

def make_single(volume_uL, rate_mlh):
    """
    単独液滴用の PPL スクリプトを生成する関数
    """
    ppl = f"""
; Single droplet injection
; 体積: {volume_uL} µL
; 流量: {rate_mlh} mL/h
; 注入方向: INF (押し出し)
VOL {volume_uL} uL       ; 単独液滴の体積（{volume_uL} µL）
RAT {rate_mlh} MH       ; 流量（{rate_mlh} mL/h）
DIR INF                 ; 注入方向（INF: 押し出し）
RUN                     ; ポンプを開始
    """
    return ppl

def make_coalescence(leading_uL, trailing_uL, rate_mlh, wait_s):
    """
    合体運動用の PPL スクリプトを生成する関数
    """
    ppl = f"""
; Coalescence experiment
; 先行液滴: {leading_uL} µL, 後続液滴: {trailing_uL} µL
; 流量: {rate_mlh} mL/h, 待機時間: {wait_s} 秒
VOL {leading_uL} uL       ; 先行液滴の体積（{leading_uL} µL）
RAT {rate_mlh} MH        ; 流量（{rate_mlh} mL/h）
DIR INF                  ; 注入方向（INF: 押し出し）
RUN                      ; 先行液滴注入開始
PAS {wait_s}             ; 後続液滴を注入する前に待機
VOL {trailing_uL} uL     ; 後続液滴の体積（{trailing_uL} µL）
RUN                      ; 後続液滴注入開始
    """
    return ppl

def load_recipe(filename):
    """
    YAML ファイルを読み込み、レシピを返す関数
    """
    with open(filename, 'r') as file:
        recipe = yaml.safe_load(file)
    return recipe

def clear_output_directory(directory):
    """
    出力ディレクトリ内のすべてのファイルを削除する関数
    """
    if os.path.exists(directory):
        # フォルダ内の全ファイルとサブディレクトリを削除
        shutil.rmtree(directory)
    os.makedirs(directory)  # 新しい空のディレクトリを作成

def save_ppl_to_file(ppl_code, filename):
    """
    PPL コードをファイルに保存する関数
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w") as file:
        file.write(ppl_code)
    print(f"Saved PPL code to {filename}")

if __name__ == "__main__":
    # 出力ディレクトリをクリア（削除してから再作成）
    output_directory = "output"
    clear_output_directory(output_directory)

    # 単独液滴実験の実行
    recipe = load_recipe("recipes/single.yml")
    
    for volume in recipe['volumes_uL']:
        print(f"Generating PPL for {volume} uL")
        ppl = make_single(volume, recipe['pump']['rate_mlh'])
        # ファイル名を動粘度ごとに分けて保存
        filename = f"{output_directory}/single_droplet/single_droplet_{volume}uL.ppl"
        save_ppl_to_file(ppl, filename)  # PPL コードをファイルに保存

    # 合体運動実験の実行
    coalescence_recipe = load_recipe("recipes/coalescence.yml")
    for lead in coalescence_recipe['leading_uL']:
        for trail in coalescence_recipe['trailing_uL'][str(lead)]:
            print(f"Generating PPL for coalescence: {lead} uL lead, {trail} uL trail")
            ppl = make_coalescence(lead, trail, coalescence_recipe['pump']['rate_mlh'], coalescence_recipe['wait_s'])
            # ファイル名を先行液滴体積ごとに分けて保存
            filename = f"{output_directory}/coalescence/{lead}uL_lead/coalescence_{lead}uL_lead_{trail}uL_trail.ppl"
            save_ppl_to_file(ppl, filename)  # PPL コードをファイルに保存
