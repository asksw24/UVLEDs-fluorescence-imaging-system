import serial
import time

from src.utils.config_parser import get_config

class FilterChangerController:
    # ... (__init__, connect, disconnectメソッドは変更なし) ...
    def __init__(self):
        print("FilterChangerControllerを初期化します...")
        try:
            config = get_config()
            self.port = config.get('FilterChanger', 'port')
            self.baudrate = config.getint('FilterChanger', 'baudrate')
            self.ser = None
            print(f"設定を読み込みました: Port={self.port}, Baudrate={self.baudrate}")
        except Exception as e:
            print(f"エラー: 設定ファイルの読み込みに失敗しました。 {e}")
            self.port = None

    def connect(self):
        if self.port is None: return False
        try:
            print(f"{self.port}への接続を試みます...")
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print("接続に成功しました。")
            return True
        except serial.SerialException as e:
            print(f"エラー: {self.port}に接続できませんでした。 詳細: {e}")
            self.ser = None
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("接続を切断しました。")
        else:
            print("INFO: 既に接続が切断されています。")

    def move_to(self, position: int):
        """
        指定されたポジションにフィルターを移動させる。
        position: 1から8の整数
        """
        if not (self.ser and self.ser.is_open):
            print("エラー: 接続されていません。")
            return False
        
        if not 1 <= position <= 8:
            print(f"エラー: ポジションは1から8の間で指定してください。指定値: {position}")
            return False
            
        try:
            # 取扱説明書p.17のコマンド形式 'Fnnn' + CR/LF
            command = f"F{position}\r\n"
            print(f"コマンド送信: {command.strip()}")
            self.ser.write(command.encode('ascii'))
            
            time.sleep(0.5)

            response = self.ser.readline().decode('ascii').strip()
            print(f"応答: {response}")
            
            if response == "OK":
                print(f"ポジション {position} への移動が完了しました。")
                return True
            else:
                print("エラー: 予期しない応答がありました。")
                return False
        except Exception as e:
            print(f"エラー: コマンドの送信中にエラーが発生しました。 {e}")
            return False

    def get_current_position(self):
        """現在のフィルターポジションを問い合わせ、数値で返す。"""
        if not (self.ser and self.ser.is_open):
            print("エラー: 接続されていません。")
            return None
        
        try:
            # 取扱説明書p.17の問い合わせ形式 'F?'
            command = "F?\r\n"
            print(f"コマンド送信: {command.strip()}")
            self.ser.write(command.encode('ascii'))
            
            time.sleep(0.2) # 応答を待つための待機時間

            # 応答 'Fxxxx' を待つ
            response = self.ser.readline().decode('ascii').strip()
            print(f"応答: {response}")
            
            # 応答 'F' から始まる文字列から数値部分を抽出
            if response.startswith("F"):
                position = int(response[1:]) # 'F'の次の文字からを整数に変換
                print(f"現在のポジションは {position} です。")
                return position
            else:
                print("エラー: 予期しない応答形式でした。")
                return None
        except Exception as e:
            print(f"エラー: 問い合わせ中にエラーが発生しました。 {e}")
            return None

# --- このファイルが直接実行された場合のテストコード ---
if __name__ == '__main__':
    fc_controller = FilterChangerController()
    
    if fc_controller.port:
        print("\n--- フィルターチェンジャーの動作テストを開始します ---")
        
        if fc_controller.connect():
            print("\nステップ1: ポジション3へ移動します。")
            fc_controller.move_to(3)
            
            time.sleep(2) # 2秒待機
            
            print("\nステップ2: ポジション1へ戻します。")
            fc_controller.move_to(1)
            
            time.sleep(2) # 2秒待機
            
            fc_controller.disconnect()
            
        print("--- テストが完了しました ---")