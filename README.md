# 🎤 Vietnamese TTS Studio

Ứng dụng desktop chuyển văn bản tiếng Việt thành giọng nói, sử dụng **Microsoft Edge TTS** — hoàn toàn miễn phí, không cần API key.

## ✨ Tính năng

- 🎙️ **2 giọng Việt**: HoaiMy (Nữ) & NamMinh (Nam)
- ⚙️ **Tùy chỉnh**: tốc độ, cao độ, âm lượng
- 🎧 **Nghe thử ngay**: nhập text → nghe trực tiếp
- 📊 **Xử lý hàng loạt**: tải CSV/Excel → chuyển nhiều phần cùng lúc
- ✅ **Chọn phần**: chọn/bỏ chọn từng phần trước khi chuyển đổi
- 📚 **Master audiobook**: gộp thành 1 file MP3 với chapter markers
- 📝 **Phụ đề tự động**: tạo file SRT cho từng phần
- 🔄 **Tự thử lại**: retry 3 lần khi lỗi mạng

## 🚀 Cài đặt & chạy

### Yêu cầu
- **Python 3.8+**
- Windows (có thể chạy trên macOS/Linux nhưng chưa test)

### Chạy nhanh (Windows)
```
run_gui.bat
```
Script sẽ tự cài thư viện cần thiết rồi mở ứng dụng.

### Chạy thủ công
```bash
pip install -r requirements_gui.txt
python tts_gui.py
```

## 📁 Cấu trúc dự án

```
├── tts_gui.py              # Giao diện chính
├── tts_engine.py            # Engine TTS (edge-tts)
├── audio_player.py          # Trình phát audio
├── audiobook_merger.py      # Gộp audiobook + chapter markers
├── subtitle_composer.py     # Tạo phụ đề SRT
├── excel_processor.py       # Đọc file CSV/Excel
├── run_gui.bat              # Khởi chạy trên Windows
├── requirements_gui.txt     # Thư viện cần cài
├── samples/                 # File mẫu
│   └── example_data.csv
└── output/                  # Thư mục lưu file (tự tạo)
    ├── audio/               # File MP3
    └── subtitles/           # File SRT
```

## 📊 Định dạng file CSV/Excel

File cần có 6 cột:

| Cột | Mô tả |
|-----|-------|
| ID | Mã định danh |
| Title | Tên chương/phần |
| Part | Số thứ tự phần |
| Source Text (Chinese) | Bản gốc (tùy chọn) |
| QuickTrans (Draft) | Bản nháp (tùy chọn) |
| AI Result (Vietnamese) | **Văn bản tiếng Việt để đọc** |

Xem file mẫu tại `samples/example_data.csv`.

## 🛠️ Công nghệ

- [edge-tts](https://github.com/rany2/edge-tts) — Microsoft Edge TTS engine
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern GUI framework
- [pygame](https://www.pygame.org/) — Audio playback
- [pydub](https://github.com/jiaaro/pydub) + [mutagen](https://github.com/quodlibet/mutagen) — Audio processing

## 📄 License

Dự án cá nhân, sử dụng edge-tts theo [GPL-3.0](LICENSE).
