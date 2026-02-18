#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle Composer for Merged Audio Files
Công cụ ghép phụ đề cho các file audio đã gộp
"""

from pathlib import Path
from typing import List, Dict
import re


class SubtitleComposer:
    """
    Compose merged subtitle files with time offset adjustments
    Ghép các file phụ đề với điều chỉnh offset thời gian
    """
    
    def __init__(self):
        """Initialize subtitle composer"""
        self.chapters = []  # List of chapter data with timing info
        
    def add_chapter(
        self,
        subtitle_path: str,
        chapter_id: str,
        duration_seconds: float
    ):
        """
        Add a chapter's subtitle to the composition queue
        Thêm phụ đề của một chương vào hàng đợi ghép
        
        Args:
            subtitle_path: Path to chapter's SRT file
            chapter_id: Unique identifier for the chapter
            duration_seconds: Duration of the chapter's audio
        """
        self.chapters.append({
            'subtitle_path': subtitle_path,
            'chapter_id': chapter_id,
            'duration': duration_seconds,
            'offset': 0.0  # Will be calculated
        })
    
    def calculate_offsets(self):
        """
        Calculate time offsets for each chapter
        Tính toán offset thời gian cho từng chương
        """
        cumulative_time = 0.0
        
        for chapter in self.chapters:
            chapter['offset'] = cumulative_time
            cumulative_time += chapter['duration']
    
    def compose_master_subtitle(self, output_path: str) -> bool:
        """
        Compose master subtitle file from all chapters
        Ghép file phụ đề tổng từ tất cả các chương
        
        Args:
            output_path: Path for output master SRT file
            
        Returns:
            True if successful
        """
        try:
            # Calculate offsets / Tính offset
            self.calculate_offsets()
            
            # Prepare output / Chuẩn bị output
            master_content = []
            subtitle_index = 1
            
            # Process each chapter / Xử lý từng chương
            for chapter in self.chapters:
                subtitle_path = chapter['subtitle_path']
                offset_ms = int(chapter['offset'] * 1000)  # Convert to milliseconds
                
                if not Path(subtitle_path).exists():
                    print(f"⚠️ Không tìm thấy file phụ đề: {subtitle_path}")
                    continue
                
                # Read chapter subtitle / Đọc phụ đề chương
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse and adjust timestamps / Parse và điều chỉnh timestamp
                adjusted_blocks = self._adjust_subtitle_timing(
                    content, offset_ms, subtitle_index
                )
                
                master_content.extend(adjusted_blocks)
                subtitle_index += len(adjusted_blocks)
            
            # Write master file / Ghi file tổng
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(master_content))
            
            print(f"✅ Đã tạo file phụ đề tổng: {output_path}")
            print(f"   📊 Tổng số chương: {len(self.chapters)}")
            print(f"   📊 Tổng số subtitle: {subtitle_index - 1}")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi ghép phụ đề: {e}")
            return False
    
    def _adjust_subtitle_timing(
        self,
        srt_content: str,
        offset_ms: int,
        start_index: int
    ) -> List[str]:
        """
        Adjust subtitle timing with offset and reindex
        Điều chỉnh thời gian phụ đề với offset và đánh số lại
        
        Args:
            srt_content: Original SRT content
            offset_ms: Time offset in milliseconds
            start_index: Starting subtitle index
            
        Returns:
            List of adjusted subtitle blocks
        """
        # Split into blocks / Tách thành các khối
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        adjusted_blocks = []
        
        current_index = start_index
        
        for block in blocks:
            if not block.strip():
                continue
            
            lines = block.strip().split('\n')
            
            if len(lines) < 2:
                continue
            
            # Parse timing line (format: 00:00:00,000 --> 00:00:01,000)
            timing_line = lines[1] if len(lines) > 1 else lines[0]
            
            if '-->' in timing_line:
                # Extract timestamps / Trích xuất timestamp
                parts = timing_line.split('-->')
                start_time = parts[0].strip()
                end_time = parts[1].strip()
                
                # Adjust timestamps / Điều chỉnh timestamp
                new_start = self._add_offset_to_timestamp(start_time, offset_ms)
                new_end = self._add_offset_to_timestamp(end_time, offset_ms)
                
                # Rebuild block with new index and timing
                new_block = f"{current_index}\n{new_start} --> {new_end}"
                
                # Add subtitle text / Thêm text phụ đề
                if len(lines) > 2:
                    subtitle_text = '\n'.join(lines[2:])
                    new_block += f"\n{subtitle_text}"
                
                adjusted_blocks.append(new_block)
                current_index += 1
        
        return adjusted_blocks
    
    @staticmethod
    def _add_offset_to_timestamp(timestamp: str, offset_ms: int) -> str:
        """
        Add millisecond offset to SRT timestamp
        Thêm offset (mili giây) vào timestamp SRT
        
        Args:
            timestamp: Original timestamp (HH:MM:SS,mmm)
            offset_ms: Offset in milliseconds
            
        Returns:
            Adjusted timestamp
        """
        # Parse timestamp / Parse timestamp
        # Format: HH:MM:SS,mmm
        match = re.match(r'(\d+):(\d+):(\d+)[,\.](\d+)', timestamp)
        
        if not match:
            return timestamp
        
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        milliseconds = int(match.group(4))
        
        # Convert to total milliseconds / Chuyển sang tổng mili giây
        total_ms = (
            hours * 3600000 +
            minutes * 60000 +
            seconds * 1000 +
            milliseconds
        )
        
        # Add offset / Thêm offset
        total_ms += offset_ms
        
        # Convert back / Chuyển ngược lại
        new_hours = total_ms // 3600000
        total_ms %= 3600000
        
        new_minutes = total_ms // 60000
        total_ms %= 60000
        
        new_seconds = total_ms // 1000
        new_milliseconds = total_ms % 1000
        
        # Format / Định dạng
        return f"{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d},{new_milliseconds:03d}"
    
    def clear(self):
        """Clear all chapters / Xóa tất cả các chương"""
        self.chapters = []


# Test the module / Kiểm tra module
if __name__ == "__main__":
    # Create test subtitle files
    test_srt_1 = """1
00:00:00,000 --> 00:00:02,500
Xin chào, đây là chương một.

2
00:00:02,500 --> 00:00:05,000
Nội dung của chương đầu tiên."""

    test_srt_2 = """1
00:00:00,000 --> 00:00:03,000
Đây là chương hai.

2
00:00:03,000 --> 00:00:06,500
Với nội dung khác nhau."""

    # Create test files
    Path('test_output/subs').mkdir(parents=True, exist_ok=True)
    
    with open('test_output/subs/chapter1.srt', 'w', encoding='utf-8') as f:
        f.write(test_srt_1)
    
    with open('test_output/subs/chapter2.srt', 'w', encoding='utf-8') as f:
        f.write(test_srt_2)
    
    # Test composition
    composer = SubtitleComposer()
    composer.add_chapter('test_output/subs/chapter1.srt', 'ch1', 5.0)
    composer.add_chapter('test_output/subs/chapter2.srt', 'ch2', 6.5)
    
    print("🎬 Bắt đầu ghép phụ đề...")
    success = composer.compose_master_subtitle('test_output/master.srt')
    
    if success:
        print("\n✅ Đã tạo file phụ đề tổng!")
        with open('test_output/master.srt', 'r', encoding='utf-8') as f:
            print("\n📄 Nội dung:")
            print(f.read())
