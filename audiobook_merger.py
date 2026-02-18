#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audiobook Merger - Combine multiple MP3 chapters into one file with chapter markers
Module gộp audiobook - Gộp nhiều chương MP3 thành 1 file với chapter markers
"""

from pathlib import Path
from typing import List, Dict, Optional, Callable
from pydub import AudioSegment
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, CTOC, CHAP, TIT2, CTOCFlags


class AudiobookMerger:
    """
    Merge multiple MP3 files into one audiobook with chapter markers
    Gộp nhiều file MP3 thành 1 audiobook với chapter markers
    """
    
    def __init__(self):
        """Initialize merger"""
        pass
    
    def merge_audiobook(
        self,
        audio_files: List[Dict],
        output_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """
        Merge multiple audio files into one with chapter markers
        Gộp nhiều file audio thành 1 với chapter markers
        
        Args:
            audio_files: List of dicts with keys: 'path', 'title', 'id'
                Example: [
                    {'path': 'chap1.mp3', 'title': 'Chương 1', 'id': 1},
                    {'path': 'chap2.mp3', 'title': 'Chương 2', 'id': 2},
                ]
            output_path: Path for output audiobook file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with success status and metadata
        """
        try:
            if progress_callback:
                progress_callback(f"🎵 Bắt đầu gộp {len(audio_files)} chương thành audiobook...")
            
            # Step 1: Concatenate all audio files / Bước 1: Nối tất cả file audio
            combined_audio = AudioSegment.empty()
            chapter_info = []
            current_position_ms = 0
            
            for idx, audio_file in enumerate(audio_files, 1):
                if progress_callback:
                    progress_callback(f"  [{idx}/{len(audio_files)}] Thêm: {audio_file['title']}")
                
                # Load audio segment
                audio_path = Path(audio_file['path'])
                if not audio_path.exists():
                    if progress_callback:
                        progress_callback(f"  ⚠️ Bỏ qua (file không tồn tại): {audio_path.name}")
                    continue
                
                segment = AudioSegment.from_mp3(str(audio_path))
                duration_ms = len(segment)
                
                # Store chapter info
                chapter_info.append({
                    'id': audio_file['id'],
                    'title': audio_file['title'],
                    'start_ms': current_position_ms,
                    'end_ms': current_position_ms + duration_ms,
                    'duration_ms': duration_ms
                })
                
                # Add to combined audio
                combined_audio += segment
                current_position_ms += duration_ms
            
            if len(chapter_info) == 0:
                return {
                    'success': False,
                    'error': 'Không có file audio hợp lệ để gộp'
                }
            
            # Step 2: Export combined audio / Bước 2: Export audio đã gộp
            if progress_callback:
                progress_callback(f"💾 Đang lưu file audiobook ({len(chapter_info)} chương)...")
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            combined_audio.export(
                output_path,
                format="mp3",
                bitrate="128k"
            )
            
            # Step 3: Add chapter markers / Bước 3: Thêm chapter markers
            if progress_callback:
                progress_callback(f"📑 Đang thêm {len(chapter_info)} chapter markers...")
            
            self.add_chapter_markers(output_path, chapter_info)
            
            # Calculate statistics / Tính toán thống kê
            total_duration_sec = current_position_ms / 1000
            hours = int(total_duration_sec // 3600)
            minutes = int((total_duration_sec % 3600) // 60)
            seconds = int(total_duration_sec % 60)
            
            if progress_callback:
                progress_callback(f"✅ Hoàn thành audiobook!")
                progress_callback(f"   📊 Tổng: {len(chapter_info)} chương")
                progress_callback(f"   ⏱️ Thời lượng: {hours}h {minutes}m {seconds}s")
                progress_callback(f"   📁 File: {Path(output_path).name}")
            
            return {
                'success': True,
                'output_path': output_path,
                'total_chapters': len(chapter_info),
                'total_duration_ms': current_position_ms,
                'total_duration_readable': f"{hours}h {minutes}m {seconds}s",
                'chapter_info': chapter_info
            }
            
        except Exception as e:
            error_msg = f"❌ Lỗi khi gộp audiobook: {e}"
            if progress_callback:
                progress_callback(error_msg)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_chapter_markers(self, audio_path: str, chapter_info: List[Dict]):
        """
        Add ID3v2 chapter markers (CHAP + CTOC) to MP3 file
        Thêm chapter markers ID3v2 vào file MP3
        
        Args:
            audio_path: Path to MP3 file
            chapter_info: List of chapter dicts with start_ms, end_ms, title
        """
        try:
            # Load or create ID3 tags
            try:
                audio = MP3(audio_path, ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
            except:
                audio = MP3(audio_path)
                audio.add_tags()
            
            # Create CHAP frames for each chapter / Tạo CHAP frames cho từng chương
            chapter_element_ids = []
            
            for idx, chapter in enumerate(chapter_info, 1):
                element_id = f"chap{idx:03d}".encode('utf-8')
                chapter_element_ids.append(element_id)
                
                # Create CHAP frame
                chap = CHAP(
                    encoding=3,  # UTF-8
                    element_id=element_id,
                    start_time=chapter['start_ms'],
                    end_time=chapter['end_ms'],
                    start_offset=0xFFFFFFFF,  # Not used
                    end_offset=0xFFFFFFFF,    # Not used
                    sub_frames=[
                        TIT2(encoding=3, text=[chapter['title']])
                    ]
                )
                
                audio.tags.add(chap)
            
            # Create CTOC frame (Table of Contents) / Tạo CTOC frame
            ctoc = CTOC(
                encoding=3,  # UTF-8
                element_id=b'toc',
                flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
                child_element_ids=chapter_element_ids,
                sub_frames=[
                    TIT2(encoding=3, text=['Audiobook Chapters'])
                ]
            )
            
            audio.tags.add(ctoc)
            
            # Save tags / Lưu tags
            audio.save()
            
        except Exception as e:
            print(f"⚠️ Lỗi khi thêm chapter markers: {e}")
            raise
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get accurate audio duration in seconds
        Lấy thời lượng audio chính xác (giây)
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            audio = MP3(audio_path)
            return audio.info.length
        except Exception as e:
            print(f"⚠️ Không thể lấy duration: {e}")
            # Fallback to file size estimate
            file_size = Path(audio_path).stat().st_size
            return file_size / 24000


# Test the module / Kiểm tra module
if __name__ == "__main__":
    def progress(msg):
        print(msg)
    
    # Example usage / Ví dụ sử dụng
    merger = AudiobookMerger()
    
    # Mock data for testing
    test_files = [
        {'path': 'output/audio/chap1.mp3', 'title': 'Chương 1 - Khởi đầu', 'id': 1},
        {'path': 'output/audio/chap2.mp3', 'title': 'Chương 2 - Cuộc gặp gỡ', 'id': 2},
    ]
    
    print("AudiobookMerger module loaded successfully!")
    print("Sử dụng trong GUI để tạo master audiobook file với chapter markers.")
