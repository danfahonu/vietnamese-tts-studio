#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietnamese TTS Studio — Ứng dụng chuyển văn bản tiếng Việt thành giọng nói
Phiên bản 2.0 — Giao diện chuyên nghiệp
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
from typing import Optional
import pandas as pd
import tempfile
import shutil
import time

# Import project modules
from excel_processor import ExcelProcessor
from tts_engine import TTSEngine
from subtitle_composer import SubtitleComposer
from audio_player import AudioPlayer, PlayerState
from audiobook_merger import AudiobookMerger


# ═══════════════════════════════════════════════════════════════
# THIẾT KẾ: Bảng màu & hằng số giao diện
# ═══════════════════════════════════════════════════════════════

class Theme:
    """Bảng màu thống nhất cho toàn bộ ứng dụng"""
    # Nền chính
    BG_DARK = "#0f0f1a"
    BG_CARD = "#1a1a2e"
    BG_CARD_HOVER = "#222240"
    BG_INPUT = "#16213e"

    # Accent
    PRIMARY = "#6366f1"        # Indigo
    PRIMARY_HOVER = "#4f46e5"
    SECONDARY = "#8b5cf6"      # Purple
    SUCCESS = "#22c55e"
    SUCCESS_HOVER = "#16a34a"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    DANGER_HOVER = "#dc2626"

    # Text
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"
    TEXT_ACCENT = "#a5b4fc"

    # Borders
    BORDER = "#2a2a4a"

    # Font
    FONT_FAMILY = "Segoe UI"
    FONT_MONO = "Consolas"


# ═══════════════════════════════════════════════════════════════
# ỨNG DỤNG CHÍNH
# ═══════════════════════════════════════════════════════════════

class TTSApp(ctk.CTk):
    """
    Vietnamese TTS Studio — Ứng dụng GUI chính
    Giao diện 2 cột: Cấu hình (trái) | Dữ liệu & Xử lý (phải)
    """

    def __init__(self):
        super().__init__()

        # ── Cấu hình cửa sổ ──
        self.title("Vietnamese TTS Studio")
        self.geometry("1500x880")
        self.minsize(1200, 700)

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=Theme.BG_DARK)

        # ── Khởi tạo các module ──
        self.excel_processor = ExcelProcessor()
        self.tts_engine = TTSEngine()
        self.subtitle_composer = SubtitleComposer()
        self.audio_player = AudioPlayer()
        self.audiobook_merger = AudiobookMerger()

        # Callbacks
        self.audio_player.set_on_finish_callback(self._on_audio_finish)
        self.audio_player.set_on_state_change_callback(self._on_player_state_change)

        # ── Biến trạng thái ──
        self.output_folder = Path("output")
        self.temp_folder = Path(tempfile.gettempdir()) / "vn_tts_preview"
        self.temp_folder.mkdir(parents=True, exist_ok=True)
        self.is_processing = False
        self.current_file_path = None
        self.current_preview_audio = None
        self.row_checkboxes = []  # [(BooleanVar, row_data), ...]

        # ── Xây dựng giao diện ──
        self._build_ui()

        # Cleanup khi đóng
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ═══════════════════════════════════════════════════════════
    # XÂY DỰNG GIAO DIỆN
    # ═══════════════════════════════════════════════════════════

    def _build_ui(self):
        """Xây dựng toàn bộ giao diện"""
        self.grid_columnconfigure(0, weight=0, minsize=320)  # Sidebar trái
        self.grid_columnconfigure(1, weight=1)                # Panel chính
        self.grid_rowconfigure(0, weight=0)                   # Header
        self.grid_rowconfigure(1, weight=1)                   # Nội dung

        self._build_header()
        self._build_sidebar()
        self._build_main_panel()

    # ─────────── HEADER ───────────

    def _build_header(self):
        """Thanh tiêu đề ứng dụng"""
        header = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=0, height=70)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        # Logo + Tên
        title = ctk.CTkLabel(
            header,
            text="🎤  Vietnamese TTS Studio",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=22, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, padx=25, pady=(18, 2), sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Chuyển văn bản tiếng Việt thành giọng nói chuyên nghiệp",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_MUTED
        )
        subtitle.grid(row=1, column=0, padx=25, pady=(0, 10), sticky="w")

        # Version badge
        version = ctk.CTkLabel(
            header,
            text="v2.0",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            text_color=Theme.TEXT_MUTED,
            fg_color=Theme.BG_INPUT,
            corner_radius=6,
            width=50, height=24
        )
        version.grid(row=0, column=1, padx=25, pady=18, sticky="e")

    # ─────────── SIDEBAR TRÁI ───────────

    def _build_sidebar(self):
        """Sidebar trái: Cấu hình giọng + Nghe thử"""
        sidebar = ctk.CTkScrollableFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=0, width=320
        )
        sidebar.grid(row=1, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)

        # ── CARD: Cấu hình giọng đọc ──
        self._build_voice_config(sidebar)

        # ── CARD: Nghe thử ──
        self._build_audio_preview(sidebar)

    def _build_voice_config(self, parent):
        """Card cấu hình giọng đọc"""
        card = self._create_card(parent, "🎙️  Cấu hình giọng đọc")

        # Giọng đọc
        self._add_label(card, "Giọng đọc")
        self.voice_var = ctk.StringVar(value="HoaiMy (Nữ)")
        voice_menu = ctk.CTkOptionMenu(
            card, variable=self.voice_var,
            values=list(TTSEngine.VIETNAMESE_VOICES.keys()),
            command=self._on_voice_change,
            fg_color=Theme.BG_INPUT,
            button_color=Theme.PRIMARY,
            button_hover_color=Theme.PRIMARY_HOVER,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13),
            dropdown_font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            corner_radius=8, height=36
        )
        voice_menu.pack(pady=(0, 16), padx=16, fill="x")

        # Tốc độ đọc
        self._add_label(card, "Tốc độ đọc")
        self.rate_label = ctk.CTkLabel(
            card, text="0%",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_ACCENT
        )
        self.rate_label.pack(anchor="e", padx=16)
        self.rate_slider = self._create_slider(card, -50, 50, 0, self._on_rate_change)

        # Cao độ giọng
        self._add_label(card, "Cao độ giọng")
        self.pitch_label = ctk.CTkLabel(
            card, text="0 Hz",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_ACCENT
        )
        self.pitch_label.pack(anchor="e", padx=16)
        self.pitch_slider = self._create_slider(card, -50, 50, 0, self._on_pitch_change)

        # Âm lượng tạo file
        self._add_label(card, "Âm lượng tạo file")
        self.volume_label = ctk.CTkLabel(
            card, text="100%",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_ACCENT
        )
        self.volume_label.pack(anchor="e", padx=16)
        self.volume_slider = self._create_slider(card, 0, 100, 100, self._on_volume_change)

    def _build_audio_preview(self, parent):
        """Card nghe thử audio"""
        card = self._create_card(parent, "🎧  Nghe thử")

        # Text thử nghiệm
        self._add_label(card, "Nhập văn bản thử")
        self.test_text = ctk.CTkTextbox(
            card, height=80,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=8
        )
        self.test_text.pack(pady=(0, 12), padx=16, fill="x")
        self.test_text.insert(
            "1.0",
            "Xin chào! Đây là bài kiểm tra giọng đọc tiếng Việt. "
            "Bạn có thể nghe thử ngay lập tức."
        )

        # Nút tạo & nghe
        self.preview_btn = ctk.CTkButton(
            card,
            text="▶  Tạo và nghe thử",
            command=self._generate_and_play_preview,
            height=40,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=8
        )
        self.preview_btn.pack(pady=(0, 12), padx=16, fill="x")

        # Điều khiển phát
        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.pack(pady=(0, 8), padx=16, fill="x")
        controls.grid_columnconfigure((0, 1, 2), weight=1)

        self.play_btn = ctk.CTkButton(
            controls, text="▶", width=55, height=36,
            command=self._play_audio,
            fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
            corner_radius=8, state="disabled",
            font=ctk.CTkFont(size=14)
        )
        self.play_btn.grid(row=0, column=0, padx=2)

        self.pause_btn = ctk.CTkButton(
            controls, text="⏸", width=55, height=36,
            command=self._pause_audio,
            fg_color=Theme.WARNING, hover_color="#d97706",
            corner_radius=8, state="disabled",
            font=ctk.CTkFont(size=14)
        )
        self.pause_btn.grid(row=0, column=1, padx=2)

        self.stop_btn = ctk.CTkButton(
            controls, text="⏹", width=55, height=36,
            command=self._stop_audio,
            fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER,
            corner_radius=8, state="disabled",
            font=ctk.CTkFont(size=14)
        )
        self.stop_btn.grid(row=0, column=2, padx=2)

        # Âm lượng phát
        self._add_label(card, "🔊 Âm lượng phát")
        self.playback_vol_label = ctk.CTkLabel(
            card, text="100%",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_ACCENT
        )
        self.playback_vol_label.pack(anchor="e", padx=16)
        self.playback_vol_slider = self._create_slider(
            card, 0, 100, 100, self._on_playback_volume_change
        )

        # Trạng thái phát
        self.audio_status = ctk.CTkLabel(
            card, text="⏹  Đã dừng",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.audio_status.pack(pady=(4, 16), padx=16)

    # ─────────── PANEL CHÍNH (PHẢI) ───────────

    def _build_main_panel(self):
        """Panel chính bên phải: Toolbar → Bảng dữ liệu → Xử lý → Log"""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(8, 16))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)   # Bảng dữ liệu chiếm nhiều nhất
        main.grid_rowconfigure(3, weight=0, minsize=160)  # Log panel

        self._build_toolbar(main)
        self._build_data_table(main)
        self._build_processing_panel(main)
        self._build_log_panel(main)

    def _build_toolbar(self, parent):
        """Thanh công cụ: Tải file + Chọn thư mục output"""
        toolbar = ctk.CTkFrame(parent, fg_color=Theme.BG_CARD, corner_radius=10)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.grid_columnconfigure(2, weight=1)

        # ── Hàng 1: Tải file dữ liệu ──
        ctk.CTkLabel(
            toolbar,
            text="📂  Tải file dữ liệu",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).grid(row=0, column=0, padx=16, pady=(14, 0), sticky="w", columnspan=3)

        file_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        file_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(6, 12))
        file_row.grid_columnconfigure(2, weight=1)

        csv_btn = ctk.CTkButton(
            file_row,
            text="📊  Tải CSV / Excel",
            command=self._load_excel_file,
            width=170, height=40,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=8
        )
        csv_btn.grid(row=0, column=0, padx=(0, 8))

        txt_btn = ctk.CTkButton(
            file_row,
            text="📄  Tải file Text",
            command=self._load_text_file,
            width=150, height=40,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            fg_color=Theme.SECONDARY,
            hover_color="#7c3aed",
            corner_radius=8
        )
        txt_btn.grid(row=0, column=1, padx=(0, 12))

        self.file_info = ctk.CTkLabel(
            file_row, text="Chưa tải file nào",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.file_info.grid(row=0, column=2, sticky="w")

        # ── Đường phân cách ──
        sep = ctk.CTkFrame(toolbar, fg_color=Theme.BORDER, height=1)
        sep.grid(row=2, column=0, columnspan=3, sticky="ew", padx=16)

        # ── Hàng 2: Thư mục lưu file output ──
        out_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        out_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=16, pady=12)
        out_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            out_row,
            text="💾  Thư mục lưu file:",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).grid(row=0, column=0, padx=(0, 10))

        self.output_label = ctk.CTkLabel(
            out_row, text=str(self.output_folder),
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_ACCENT,
            anchor="w"
        )
        self.output_label.grid(row=0, column=1, sticky="w", padx=(0, 10))

        out_btn = ctk.CTkButton(
            out_row,
            text="📁  Chọn thư mục khác",
            command=self._select_output_folder,
            width=170, height=34,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=8
        )
        out_btn.grid(row=0, column=2)

    def _build_data_table(self, parent):
        """Bảng chọn các phần cần chuyển đổi"""
        table_card = ctk.CTkFrame(parent, fg_color=Theme.BG_CARD, corner_radius=10)
        table_card.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(1, weight=1)

        # ── Header bảng ──
        header = ctk.CTkFrame(table_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="📋  Chọn các phần cần chuyển đổi",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w")

        # Label đếm số lượng đã chọn
        self.selection_count = ctk.CTkLabel(
            header,
            text="Đã chọn: 0 / 0 phần",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.selection_count.grid(row=0, column=1, sticky="e", padx=(10, 8))

        # Nút chọn tất cả
        sel_all_btn = ctk.CTkButton(
            header,
            text="✅ Chọn tất cả",
            command=self._select_all,
            width=115, height=28,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            corner_radius=6
        )
        sel_all_btn.grid(row=0, column=2, padx=(0, 4))

        # Nút bỏ chọn
        desel_btn = ctk.CTkButton(
            header,
            text="❌ Bỏ chọn",
            command=self._deselect_all,
            width=100, height=28,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            fg_color=Theme.DANGER,
            hover_color=Theme.DANGER_HOVER,
            corner_radius=6
        )
        desel_btn.grid(row=0, column=3)

        # ── Danh sách phần (scrollable) ──
        self.data_scroll = ctk.CTkScrollableFrame(
            table_card,
            fg_color=Theme.BG_INPUT,
            corner_radius=8
        )
        self.data_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))

        # Placeholder khi chưa có dữ liệu
        self.placeholder = ctk.CTkLabel(
            self.data_scroll,
            text="📂  Hãy tải file CSV, Excel hoặc Text để bắt đầu",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13),
            text_color=Theme.TEXT_MUTED
        )
        self.placeholder.pack(pady=40)

    def _build_processing_panel(self, parent):
        """Panel xử lý hàng loạt: nút chuyển đổi + progress"""
        proc_card = ctk.CTkFrame(parent, fg_color=Theme.BG_CARD, corner_radius=10)
        proc_card.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        proc_card.grid_columnconfigure(1, weight=1)

        # Nút chuyển đổi
        self.process_btn = ctk.CTkButton(
            proc_card,
            text="🚀  Chuyển đổi MP3",
            command=self._process_selected,
            width=200, height=44,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=10
        )
        self.process_btn.grid(row=0, column=0, padx=16, pady=14)

        # Checkbox tạo audiobook
        self.create_master_var = ctk.BooleanVar(value=True)
        master_cb = ctk.CTkCheckBox(
            proc_card,
            text="Tạo master audiobook (gộp 1 file + chapter markers)",
            variable=self.create_master_var,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_SECONDARY,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            border_color=Theme.BORDER
        )
        master_cb.grid(row=0, column=1, padx=10, pady=14, sticky="w")

        # Thống kê
        self.stats_label = ctk.CTkLabel(
            proc_card,
            text="Tổng: 0  |  Thành công: 0  |  Thất bại: 0",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.stats_label.grid(row=0, column=2, padx=(0, 16), sticky="e")

        # Progress bar
        progress_frame = ctk.CTkFrame(proc_card, fg_color="transparent")
        progress_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(0, 12))
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            corner_radius=6,
            height=10,
            progress_color=Theme.PRIMARY,
            fg_color=Theme.BG_INPUT
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0 / 0",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=11),
            text_color=Theme.TEXT_MUTED, width=70
        )
        self.progress_label.grid(row=0, column=1, padx=(10, 0))

    def _build_log_panel(self, parent):
        """Panel nhật ký xử lý"""
        log_card = ctk.CTkFrame(parent, fg_color=Theme.BG_CARD, corner_radius=10)
        log_card.grid(row=3, column=0, sticky="nsew")
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_card,
            text="📋  Nhật ký xử lý",
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        self.log_text = ctk.CTkTextbox(
            log_card,
            font=ctk.CTkFont(family=Theme.FONT_MONO, size=11),
            fg_color=Theme.BG_INPUT,
            corner_radius=8,
            border_width=0
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))

    # ═══════════════════════════════════════════════════════════
    # TIỆN ÍCH TẠO WIDGET
    # ═══════════════════════════════════════════════════════════

    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        """Tạo card với tiêu đề — dùng cho sidebar"""
        card = ctk.CTkFrame(
            parent, fg_color=Theme.BG_CARD,
            border_color=Theme.BORDER, border_width=1,
            corner_radius=10
        )
        card.pack(pady=(12, 0), padx=12, fill="x")

        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(pady=(14, 10), padx=16, anchor="w")

        return card

    def _add_label(self, parent, text: str):
        """Thêm label nhỏ trong card"""
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=16, pady=(4, 2))

    def _create_slider(self, parent, from_, to, default, command) -> ctk.CTkSlider:
        """Tạo slider thống nhất style"""
        slider = ctk.CTkSlider(
            parent, from_=from_, to=to,
            command=command,
            progress_color=Theme.PRIMARY,
            fg_color=Theme.BG_INPUT,
            button_color=Theme.SECONDARY,
            button_hover_color=Theme.PRIMARY
        )
        slider.set(default)
        slider.pack(pady=(0, 14), padx=16, fill="x")
        return slider

    # ═══════════════════════════════════════════════════════════
    # XỬ LÝ SỰ KIỆN — CẤU HÌNH GIỌNG
    # ═══════════════════════════════════════════════════════════

    def _on_voice_change(self, choice):
        """Thay đổi giọng đọc"""
        self.tts_engine.set_voice(choice)
        self.log(f"✅ Đã chọn giọng: {choice}")

    def _on_rate_change(self, value):
        """Thay đổi tốc độ"""
        rate = int(value)
        self.tts_engine.set_rate(rate)
        self.rate_label.configure(text=f"{rate:+d}%")

    def _on_pitch_change(self, value):
        """Thay đổi cao độ"""
        pitch = int(value)
        self.tts_engine.set_pitch(pitch)
        self.pitch_label.configure(text=f"{pitch:+d} Hz")

    def _on_volume_change(self, value):
        """Thay đổi âm lượng tạo file"""
        vol = int(value)
        self.tts_engine.set_volume(vol)
        self.volume_label.configure(text=f"{vol}%")

    def _on_playback_volume_change(self, value):
        """Thay đổi âm lượng phát"""
        vol = int(value)
        self.audio_player.set_volume(vol / 100.0)
        self.playback_vol_label.configure(text=f"{vol}%")

    def _on_player_state_change(self, state: PlayerState):
        """Cập nhật UI theo trạng thái player"""
        if state == PlayerState.PLAYING:
            self.audio_status.configure(text="▶  Đang phát", text_color=Theme.SUCCESS)
            self.play_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
        elif state == PlayerState.PAUSED:
            self.audio_status.configure(text="⏸  Tạm dừng", text_color=Theme.WARNING)
            self.play_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        elif state == PlayerState.STOPPED:
            self.audio_status.configure(text="⏹  Đã dừng", text_color=Theme.TEXT_MUTED)
            self.play_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")

    def _on_audio_finish(self):
        """Khi phát xong audio"""
        self.log("✅ Phát xong audio nghe thử")

    # ═══════════════════════════════════════════════════════════
    # XỬ LÝ SỰ KIỆN — BẢNG DỮ LIỆU
    # ═══════════════════════════════════════════════════════════

    def _populate_data_table(self):
        """Điền bảng dữ liệu với checkbox cho từng phần"""
        # Xóa nội dung cũ
        for widget in self.data_scroll.winfo_children():
            widget.destroy()
        self.row_checkboxes = []

        rows = self.excel_processor.get_rows_for_processing()
        if not rows:
            # Hiện placeholder nếu không có dữ liệu
            self.placeholder = ctk.CTkLabel(
                self.data_scroll,
                text="📂  Không tìm thấy dữ liệu trong file",
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=13),
                text_color=Theme.TEXT_MUTED
            )
            self.placeholder.pack(pady=40)
            return

        for i, row in enumerate(rows):
            var = ctk.BooleanVar(value=True)

            # Cắt ngắn text để hiện preview
            text_preview = row['text'][:90].replace('\n', ' ').replace('\r', '')
            if len(row['text']) > 90:
                text_preview += '...'

            # Tạo frame cho mỗi row
            row_frame = ctk.CTkFrame(
                self.data_scroll,
                fg_color=Theme.BG_CARD if i % 2 == 0 else "transparent",
                corner_radius=6
            )
            row_frame.pack(fill="x", padx=4, pady=1)

            cb = ctk.CTkCheckBox(
                row_frame,
                text=f"  [{row['id']}]  {row['title']}  (Phần {row['part']})  —  {text_preview}",
                variable=var,
                font=ctk.CTkFont(family=Theme.FONT_FAMILY, size=12),
                text_color=Theme.TEXT_PRIMARY,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                border_color=Theme.BORDER,
                command=self._update_selection_count
            )
            cb.pack(pady=5, padx=10, anchor="w", fill="x")

            self.row_checkboxes.append((var, row))

        self._update_selection_count()

    def _get_selected_rows(self):
        """Lấy danh sách các phần đã được chọn"""
        return [row for var, row in self.row_checkboxes if var.get()]

    def _select_all(self):
        """Chọn tất cả các phần"""
        for var, _ in self.row_checkboxes:
            var.set(True)
        self._update_selection_count()

    def _deselect_all(self):
        """Bỏ chọn tất cả các phần"""
        for var, _ in self.row_checkboxes:
            var.set(False)
        self._update_selection_count()

    def _update_selection_count(self):
        """Cập nhật label đếm số phần đã chọn"""
        selected = len(self._get_selected_rows())
        total = len(self.row_checkboxes)
        self.selection_count.configure(
            text=f"Đã chọn: {selected} / {total} phần",
            text_color=Theme.SUCCESS if selected > 0 else Theme.DANGER
        )

    # ═══════════════════════════════════════════════════════════
    # XỬ LÝ SỰ KIỆN — TẢI FILE
    # ═══════════════════════════════════════════════════════════

    def _load_excel_file(self):
        """Tải file CSV hoặc Excel"""
        file_path = filedialog.askopenfilename(
            title="Chọn file dữ liệu",
            filetypes=[
                ("File dữ liệu", "*.xlsx *.xls *.csv"),
                ("File CSV", "*.csv"),
                ("File Excel", "*.xlsx *.xls"),
                ("Tất cả", "*.*")
            ]
        )

        if file_path:
            if self.excel_processor.load_excel(file_path):
                self.current_file_path = file_path
                row_count = self.excel_processor.get_row_count()
                self.file_info.configure(
                    text=f"✅  {Path(file_path).name}  ({row_count} phần)",
                    text_color=Theme.SUCCESS
                )
                self.log(f"📊 Đã tải: {Path(file_path).name} ({row_count} phần)")

                # Điền bảng chọn phần
                self._populate_data_table()

                # Cập nhật thống kê
                self._update_stats(total=row_count, processed=0, failed=0)
            else:
                messagebox.showerror(
                    "Lỗi tải file",
                    "Không thể đọc file. Vui lòng kiểm tra định dạng file.\n\n"
                    "Yêu cầu các cột: ID, Title, Part, Source Text (Chinese), "
                    "QuickTrans (Draft), AI Result (Vietnamese)"
                )

    def _load_text_file(self):
        """Tải file text"""
        file_path = filedialog.askopenfilename(
            title="Chọn file văn bản",
            filetypes=[("File Text", "*.txt"), ("Tất cả", "*.*")]
        )

        if file_path:
            if self.excel_processor.load_text_file(file_path):
                self.current_file_path = file_path
                self.file_info.configure(
                    text=f"✅  {Path(file_path).name}",
                    text_color=Theme.SUCCESS
                )
                self.log(f"📄 Đã tải: {Path(file_path).name}")

                # Điền bảng chọn phần
                self._populate_data_table()

                # Cập nhật thống kê
                self._update_stats(total=1, processed=0, failed=0)
            else:
                messagebox.showerror("Lỗi tải file", "Không thể đọc file text.")

    def _select_output_folder(self):
        """Chọn thư mục lưu file output"""
        folder = filedialog.askdirectory(title="Chọn thư mục lưu file")
        if folder:
            self.output_folder = Path(folder)
            self.output_label.configure(text=str(self.output_folder))
            self.log(f"📂 Thư mục output: {self.output_folder}")

    # ═══════════════════════════════════════════════════════════
    # XỬ LÝ SỰ KIỆN — NGHE THỬ
    # ═══════════════════════════════════════════════════════════

    def _generate_and_play_preview(self):
        """Tạo và phát audio nghe thử"""
        test_text = self.test_text.get("1.0", "end").strip()

        if not test_text:
            messagebox.showwarning("Chưa có văn bản", "Vui lòng nhập văn bản cần nghe thử.")
            return

        self.log("🎤 Đang tạo audio nghe thử...")
        self.preview_btn.configure(state="disabled", text="⏳  Đang tạo...")

        # Dừng audio cũ
        self.audio_player.stop()

        def _thread():
            try:
                time.sleep(0.1)
                preview_path = self.temp_folder / "preview.mp3"
                result = self.tts_engine.generate_audio_sync(
                    text=test_text,
                    output_audio_path=str(preview_path),
                    progress_callback=self.log
                )

                if result['success']:
                    self.current_preview_audio = preview_path
                    self.log(f"✅ Đã tạo audio nghe thử")

                    if self.audio_player.load(str(preview_path)):
                        self.audio_player.play()
                        self.log("▶ Đang phát...")
                    else:
                        messagebox.showerror("Lỗi", "Không thể phát audio nghe thử")
                else:
                    messagebox.showerror(
                        "Lỗi tạo audio",
                        f"Không thể tạo audio: {result.get('error', 'Không rõ nguyên nhân')}"
                    )
            finally:
                self.preview_btn.configure(state="normal", text="▶  Tạo và nghe thử")

        threading.Thread(target=_thread, daemon=True).start()

    def _play_audio(self):
        """Phát audio nghe thử"""
        self.audio_player.play()
        self.log("▶ Phát audio")

    def _pause_audio(self):
        """Tạm dừng audio"""
        self.audio_player.pause()
        self.log("⏸ Tạm dừng")

    def _stop_audio(self):
        """Dừng audio"""
        self.audio_player.stop()
        self.log("⏹ Đã dừng")

    # ═══════════════════════════════════════════════════════════
    # XỬ LÝ HÀNG LOẠT
    # ═══════════════════════════════════════════════════════════

    def _process_selected(self):
        """Xử lý các phần đã chọn"""
        if self.is_processing:
            messagebox.showwarning("Đang xử lý", "Hệ thống đang xử lý. Vui lòng đợi.")
            return

        if not self.current_file_path:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng tải file CSV, Excel hoặc Text trước.")
            return

        rows = self._get_selected_rows()
        if not rows:
            messagebox.showwarning("Chưa chọn phần nào", "Vui lòng chọn ít nhất 1 phần để chuyển đổi.")
            return

        # Xác nhận
        response = messagebox.askyesno(
            "Xác nhận chuyển đổi",
            f"Bắt đầu chuyển đổi {len(rows)} phần đã chọn thành MP3?\n\n"
            f"Thư mục lưu: {self.output_folder}"
        )

        if not response:
            return

        self.is_processing = True
        self.process_btn.configure(state="disabled", text="⏳  Đang xử lý...")
        self.log(f"\n{'═' * 60}")
        self.log(f"🚀 BẮT ĐẦU CHUYỂN ĐỔI — {len(rows)} phần")
        self.log(f"{'═' * 60}\n")

        def _thread():
            try:
                self._batch_process(rows)
            finally:
                self.is_processing = False
                self.process_btn.configure(state="normal", text="🚀  Chuyển đổi MP3")

        threading.Thread(target=_thread, daemon=True).start()

    def _batch_process(self, rows):
        """Xử lý hàng loạt các phần đã chọn"""
        total = len(rows)
        processed = 0
        failed = 0

        # Tạo thư mục output
        audio_dir = self.output_folder / "audio"
        subtitle_dir = self.output_folder / "subtitles"
        audio_dir.mkdir(parents=True, exist_ok=True)
        subtitle_dir.mkdir(parents=True, exist_ok=True)

        # Xóa subtitle composer
        self.subtitle_composer.clear()

        for idx, row in enumerate(rows, 1):
            # Cập nhật tiến trình
            progress = idx / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"{idx} / {total}")

            # Tạo tên file
            filename = f"{row['id']}_{row['title']}_Part{row['part']}"
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()

            audio_path = audio_dir / f"{filename}.mp3"
            subtitle_path = subtitle_dir / f"{filename}.srt"

            self.log(f"\n[{idx}/{total}] Đang xử lý: {filename}")

            # Thử lại với exponential backoff
            max_retries = 3
            success = False

            for retry in range(max_retries):
                try:
                    result = self.tts_engine.generate_audio_sync(
                        text=row['text'],
                        output_audio_path=str(audio_path),
                        output_subtitle_path=str(subtitle_path),
                        progress_callback=self.log
                    )

                    if result['success']:
                        processed += 1
                        success = True

                        # Thêm vào subtitle composer
                        estimated_duration = len(row['text']) / 15
                        self.subtitle_composer.add_chapter(
                            str(subtitle_path),
                            row['id'],
                            estimated_duration
                        )
                        break
                    else:
                        error_msg = result.get('error', 'Lỗi không xác định')
                        if retry < max_retries - 1:
                            wait_time = 2 ** retry
                            self.log(f"⚠️ Lỗi: {error_msg}")
                            self.log(f"⏳ Thử lại {retry + 2}/{max_retries} sau {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            self.log(f"❌ THẤT BẠI sau {max_retries} lần: {error_msg}")
                            failed += 1

                except Exception as e:
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry
                        self.log(f"⚠️ Lỗi: {str(e)}")
                        self.log(f"⏳ Thử lại {retry + 2}/{max_retries} sau {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        self.log(f"❌ LỖI sau {max_retries} lần: {str(e)}")
                        failed += 1

            # Cập nhật thống kê
            self._update_stats(total=total, processed=processed, failed=failed)

            # Delay giữa các phần để tránh rate limit
            if idx < total:
                time.sleep(0.5)

        # Tạo phụ đề tổng
        if processed > 0:
            self.log(f"\n{'═' * 60}")
            self.log("🎬 Đang tạo file phụ đề tổng...")
            master_subtitle_path = subtitle_dir / "master_subtitle.srt"
            self.subtitle_composer.compose_master_subtitle(str(master_subtitle_path))

        # Tạo master audiobook
        if processed > 0 and self.create_master_var.get():
            self.log(f"\n{'═' * 60}")
            self.log("📚 Đang tạo master audiobook với chapter markers...")

            audio_files = []
            for row in rows:
                filename = f"{row['id']}_{row['title']}_Part{row['part']}"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
                audio_path = audio_dir / f"{filename}.mp3"

                if audio_path.exists():
                    audio_files.append({
                        'path': str(audio_path),
                        'title': row['title'],
                        'id': row['id']
                    })

            if audio_files:
                master_path = self.output_folder / "master_audiobook.mp3"
                result = self.audiobook_merger.merge_audiobook(
                    audio_files=audio_files,
                    output_path=str(master_path),
                    progress_callback=self.log
                )

                if result['success']:
                    self.log(f"\n✅ Master audiobook: {master_path.name}")
                    self.log(f"   📊 {result['total_chapters']} chương")
                    self.log(f"   ⏱️ {result['total_duration_readable']}")

        # Tổng kết
        self.log(f"\n{'═' * 60}")
        self.log("✅ HOÀN THÀNH CHUYỂN ĐỔI!")
        self.log(f"📊 Tổng: {total}")
        self.log(f"✅ Thành công: {processed}")
        self.log(f"❌ Thất bại: {failed}")
        self.log(f"📂 Thư mục: {self.output_folder}")
        if self.create_master_var.get() and processed > 0:
            self.log(f"📚 Master audiobook: master_audiobook.mp3")
        self.log(f"{'═' * 60}\n")

        summary = (
            f"Đã hoàn thành!\n\n"
            f"Tổng: {total}\n"
            f"Thành công: {processed}\n"
            f"Thất bại: {failed}\n\n"
            f"Thư mục: {self.output_folder}"
        )
        if self.create_master_var.get() and processed > 0:
            summary += "\n\n📚 Đã tạo master_audiobook.mp3 với chapter markers!"

        messagebox.showinfo("Hoàn thành", summary)

    # ═══════════════════════════════════════════════════════════
    # TIỆN ÍCH
    # ═══════════════════════════════════════════════════════════

    def _update_stats(self, total: int, processed: int, failed: int):
        """Cập nhật thống kê hiển thị"""
        self.stats_label.configure(
            text=f"Tổng: {total}  |  Thành công: {processed}  |  Thất bại: {failed}"
        )

    def log(self, message: str):
        """Thêm dòng vào nhật ký"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.update()

    def _on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        self.audio_player.stop()
        self.audio_player.cleanup()

        try:
            if self.temp_folder.exists():
                shutil.rmtree(self.temp_folder)
        except Exception as e:
            print(f"⚠️ Không thể xóa thư mục tạm: {e}")

        self.destroy()


# ═══════════════════════════════════════════════════════════════
# ĐIỂM KHỞI CHẠY
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = TTSApp()
    app.mainloop()
