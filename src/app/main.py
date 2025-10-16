import tkinter as tk
from tkinter import ttk
# config_parserをインポートするのを忘れないように
from src.utils.config_parser import get_config
from src.hardware.filter_changer import FilterChangerController
import time

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("蛍光分光画像撮影システム")
        self.geometry("1024x768")        
        
        # 1. フィルターチェンジャー用の「リモコン」を属性として作成
        self.fc_controller = FilterChangerController()

        # --- 設定ファイルから波長リストを読み込んで保持 ---
        self._load_config()
        self.create_widgets()

        # 2. 起動時にデバイスへの接続を試みるメソッドを呼び出す
        self._connect_devices()

    def _load_config(self):
        """起動時に設定ファイルを読み込み、波長リストなどを準備する"""
        try:
            config = get_config()
            self.filter_options = dict(config.items('FilterWavelengths'))
            self.led_options = [value for key, value in config.items('LedWavelengths')]
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            # デフォルト値を設定
            self.filter_options = {"1":"Error", "2":"Error"}
            self.led_options = ["Error"]

    def create_widgets(self):
        # --- メインレイアウト ---
        main_pane = ttk.PanedWindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True)

        self.control_frame = ttk.Frame(main_pane, width=450)
        main_pane.add(self.control_frame, weight=1)

        # 右側パネル（プレビューとステータス）
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=3)

        self.preview_frame = ttk.Labelframe(right_frame, text="プレビュー")
        self.preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.status_frame = ttk.Labelframe(right_frame, text="デバイス接続状態")
        self.status_frame.pack(fill="x", side="bottom", padx=5, pady=5)

        log_frame = ttk.Frame(self, height=150)
        log_frame.pack(fill="x", side="bottom")

        # --- 各要素の配置 ---
        self._create_control_widgets()
        self._create_preview_widgets()
        self._create_status_widgets()
        self._create_log_widgets(log_frame)

    def _create_control_widgets(self):
        # ... (タブの作成部分は変更なし) ...
        notebook = ttk.Notebook(self.control_frame)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        live_tab = ttk.Frame(notebook)
        auto_tab = ttk.Frame(notebook)
        notebook.add(live_tab, text="手動・ライブビュー")
        notebook.add(auto_tab, text="自動撮影")
        self._populate_live_tab(live_tab)
        self._populate_auto_tab(auto_tab)

    def _populate_live_tab(self, parent_frame):
        manual_frame = ttk.Labelframe(parent_frame, text="フィルター手動操作")
        manual_frame.pack(side="top", fill="x", padx=10, pady=10)
        button_frame = ttk.Frame(manual_frame)
        button_frame.pack(pady=5)

        # .iniファイルから読み込んだ情報でボタンを動的に生成
        for i, (pos, wavelength) in enumerate(self.filter_options.items()):
            button_text = f"{pos}: {wavelength}"
            button = ttk.Button(
                button_frame,
                text=button_text,
                width=12,
                # commandオプションで、押されたときに呼び出す関数を指定
                # lambda p=pos: ... は、どのボタン(pos)が押されたかを伝えるための書き方
                command=lambda p=pos: self._move_filter(p)
            )
            button.grid(row=i // 4, column=i % 4, padx=5, pady=5)
            
        self.current_pos_label = ttk.Label(manual_frame, text="現在位置: - (自動更新)")
        self.current_pos_label.pack(pady=5)

        live_frame = ttk.Labelframe(parent_frame, text="ライブビュー調整")
        live_frame.pack(side="top", fill="x", padx=10, pady=10)
        
        ttk.Label(live_frame, text="励起波長:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        # .iniファイルから読み込んだLED波長をリストに設定
        live_led_combo = ttk.Combobox(live_frame, width=15, values=self.led_options)
        live_led_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # ... (他のライブビューウィジェットは変更なし) ...
        ttk.Label(live_frame, text="露光時間 (ms):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        live_exp_entry = ttk.Entry(live_frame, width=18)
        live_exp_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.is_live_view = tk.BooleanVar()
        live_check = ttk.Checkbutton(live_frame, text="ライブビュー開始", variable=self.is_live_view)
        live_check.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

    def _populate_auto_tab(self, parent_frame):
        """「自動撮影」タブを作成"""
        sequence_builder_frame = ttk.Labelframe(parent_frame, text="撮影シーケンス作成")
        sequence_builder_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(sequence_builder_frame, text="励起波長:").grid(row=0, column=0, sticky="e")
        self.auto_led_combo = ttk.Combobox(sequence_builder_frame, width=15, values=self.led_options)
        self.auto_led_combo.grid(row=0, column=1, padx=5, pady=5)
        # ▼▼▼ 励起波長が選択されたら、フィルターの選択肢を更新するイベントをバインド ▼▼▼
        self.auto_led_combo.bind("<<ComboboxSelected>>", self._update_filter_options)


        ttk.Label(sequence_builder_frame, text="放射フィルター:").grid(row=1, column=0, sticky="e")
        self.auto_filter_combo = ttk.Combobox(sequence_builder_frame, width=15, values=list(self.filter_options.values()))
        self.auto_filter_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(
            sequence_builder_frame, 
            text="▼ リストに追加 ▼", 
            command=self._add_to_sequence_list
        ).grid(row=2, column=1, pady=5)

        sequence_list_frame = ttk.Labelframe(parent_frame, text="撮影シーケンスリスト")
        sequence_list_frame.pack(fill="both", expand=True, padx=10, pady=10) # fillとexpandを調整
        columns = ('led', 'filter')
        self.sequence_tree = ttk.Treeview(sequence_list_frame, columns=columns, show='headings', height=5)
        self.sequence_tree.heading('led', text='励起波長'); self.sequence_tree.heading('filter', text='放射フィルター')
        self.sequence_tree.column('led', width=120); self.sequence_tree.column('filter', width=120)
        scrollbar = ttk.Scrollbar(sequence_list_frame, orient="vertical", command=self.sequence_tree.yview)
        self.sequence_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.sequence_tree.pack(side="left", fill="both", expand=True) # fillとexpandを調整
        list_button_frame = ttk.Frame(sequence_list_frame)
        list_button_frame.pack(side="left", padx=5)
        ttk.Button(list_button_frame, text="選択を削除", command=self._delete_selected_sequence).pack(pady=2)
        ttk.Button(list_button_frame, text="全てクリア", command=self._clear_all_sequences).pack(pady=2)
        run_frame = ttk.Labelframe(parent_frame, text="撮影実行")
        run_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(run_frame, text="露光時間 (ms):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        exp_entry = ttk.Entry(run_frame, width=20)
        exp_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(run_frame, text="サンプル名:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        name_entry = ttk.Entry(run_frame, width=20)
        name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(run_frame, text="このシーケンスで撮影開始").grid(row=2, column=1, padx=5, pady=10, sticky="w")

    def _create_preview_widgets(self):
        ttk.Label(self.preview_frame, text="ここに画像が表示されます", font=("Meiryo UI", 16), anchor="center").pack(expand=True)

    def _create_status_widgets(self):
        # ▼▼▼ self.xxx_status_label = のように、属性として保持する形に変更 ▼▼▼
        self.camera_status_label = ttk.Label(self.status_frame, text="カメラ: ⚪ Disconnected")
        self.camera_status_label.pack(side="left", padx=10)
        self.filter_status_label = ttk.Label(self.status_frame, text="フィルター: ⚪ Disconnected")
        self.filter_status_label.pack(side="left", padx=10)
        self.led_status_label = ttk.Label(self.status_frame, text="LED: ⚪ Disconnected")
        self.led_status_label.pack(side="left", padx=10)

    def _create_log_widgets(self, parent_frame):
        self.log_text = tk.Text(parent_frame, height=5, state="disabled") # ユーザーの入力を無効化
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True, padx=10, pady=5)

    def _connect_devices(self):
        """起動時に各デバイスへの接続を試みる"""
        if self.fc_controller.connect():
            # 接続成功時、ステータスラベルを緑にする
            self.filter_status_label.config(text="フィルター: 🟢 Connected")
            # 現在位置を取得して表示
            self._get_filter_position()
        else:
            # 接続失敗時、ステータスラベルを赤にする
            self.filter_status_label.config(text="フィルター: 🔴 Disconnected")

    def _move_filter(self, position):
        """フィルター移動ボタンが押されたときの処理"""
        pos_int = int(position)
        if self.fc_controller.move_to(pos_int):

            # ▼▼▼ 物理的な移動が終わるのを2秒間待つ ▼▼▼
            # 取扱説明書によると最大移動時間は約2秒
            time.sleep(2)

            # 移動が成功したら、現在位置を自動で更新
            self._get_filter_position()

    def _get_filter_position(self):
        """フィルターの現在位置を取得してラベルに表示する"""
        current_pos = self.fc_controller.get_current_position()
        if current_pos is not None:
            # ラベルのテキストを更新
            self.current_pos_label.config(text=f"現在位置: {current_pos}")
        else:
            self.current_pos_label.config(text="現在位置: 取得失敗")

    def _add_to_sequence_list(self):
        """選択された波長の組み合わせをシーケンスリストに追加する"""
        led = self.auto_led_combo.get()
        filt = self.auto_filter_combo.get()

        if not led or not filt:
            print("励起波長と放射フィルターの両方を選択してください。")
            # ここでユーザーに警告メッセージを出すのが親切（将来的に実装）
            return
            
        self.sequence_tree.insert("", "end", values=(led, filt))
        self.add_log(f"シーケンス追加: LED={led}, Filter={filt}")

    def add_log(self, message):
        """ログウィジェットにタイムスタンプ付きでメッセージを追加する"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # ウィジェットを一時的に有効化してテキストを挿入
        self.log_text.config(state="normal")
        self.log_text.insert("end", log_message)
        self.log_text.config(state="disabled") # 再び読み取り専用に
        
        # 自動で一番下にスクロール
        self.log_text.see("end")

    def _parse_wavelength(self, wavelength_str):
        """'365nm'のような文字列から数値部分を抽出する。失敗した場合はNoneを返す。"""
        try:
            # 'nm'などの非数値文字をすべて取り除く
            return int(''.join(filter(str.isdigit, wavelength_str)))
        except (ValueError, TypeError):
            return None

    def _update_filter_options(self, event=None):
        """励起波長の選択に応じて、放射フィルターの選択肢を更新する"""
        selected_led_str = self.auto_led_combo.get()
        led_wavelength = self._parse_wavelength(selected_led_str)

        if led_wavelength is None:
            # 励起波長が不正な場合は、全てのフィルターを選択可能にする
            valid_filters = list(self.filter_options.values())
        else:
            # 励起波長より長い波長のフィルターのみをリストアップ
            valid_filters = []
            for pos, filt_str in self.filter_options.items():
                filt_wavelength = self._parse_wavelength(filt_str)
                if filt_wavelength is not None and filt_wavelength > led_wavelength:
                    valid_filters.append(filt_str)

        # 放射フィルターコンボボックスの選択肢を更新
        self.auto_filter_combo['values'] = valid_filters

        # 現在選択されているフィルターが、新しい選択肢リストにない場合は選択をクリア
        if self.auto_filter_combo.get() not in valid_filters:
            self.auto_filter_combo.set('')
        
        self.add_log(f"励起波長 {selected_led_str} に応じてフィルターリストを更新しました。")


    def _delete_selected_sequence(self):
        """シーケンスリストで選択されている項目を削除する"""
        selected_items = self.sequence_tree.selection()
        if not selected_items:
            self.add_log("削除するシーケンスが選択されていません。")
            return

        for item in selected_items:
            self.sequence_tree.delete(item)
        
        self.add_log(f"{len(selected_items)}件のシーケンスを削除しました。")

    def _clear_all_sequences(self):
        """シーケンスリストの全ての項目を削除する"""
        all_items = self.sequence_tree.get_children()
        if not all_items:
            self.add_log("クリアするシーケンスがありません。")
            return

        for item in all_items:
            self.sequence_tree.delete(item)
        
        self.add_log("全てのシーケンスをクリアしました。")

if __name__ == '__main__':
    app = Application()
    app.mainloop()
