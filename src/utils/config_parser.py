import configparser
from pathlib import Path

# このファイルの場所を基準に、プロジェクトのルートディレクトリを特定します
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_config():
    """設定ファイル (config/settings.ini) を読み込み、configオブジェクトを返す関数"""
    config = configparser.ConfigParser()
    config_path = PROJECT_ROOT / 'config' / 'settings.ini'
    
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
        
    config.read(config_path, encoding='utf-8')
    return config

# --- このファイルが直接実行された場合にのみ、以下のテストコードが動きます ---
if __name__ == '__main__':
    print("設定ファイルの読み込みテストを実行します...")
    
    try:
        config_data = get_config()
        
        # FilterChangerセクションの値を取得して表示
        fc_port = config_data.get('FilterChanger', 'port')
        fc_baudrate = config_data.getint('FilterChanger', 'baudrate')
        
        print(f"[FilterChanger]")
        print(f"  Port: {fc_port}")
        print(f"  Baudrate: {fc_baudrate}")
        
        # Pathsセクションの値を取得して表示
        save_dir = config_data.get('Paths', 'default_save_directory')
        print(f"[Paths]")
        print(f"  Default Save Directory: {save_dir}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")