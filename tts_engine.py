#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Engine for Vietnamese Text-to-Speech
Công cụ chuyển văn bản tiếng Việt thành giọng nói
"""

import edge_tts
import asyncio
from pathlib import Path
from typing import Optional, Dict, Callable
import re


class TTSEngine:
    """
    Text-to-Speech engine using Microsoft Edge TTS
    Công cụ TTS sử dụng Microsoft Edge TTS
    """
    
    # Vietnamese voices available / Giọng đọc tiếng Việt
    VIETNAMESE_VOICES = {
        'HoaiMy (Nữ)': 'vi-VN-HoaiMyNeural',
        'NamMinh (Nam)': 'vi-VN-NamMinhNeural',
    }
    
    def __init__(self):
        """Initialize TTS engine"""
        self.voice = 'vi-VN-HoaiMyNeural'  # Default voice
        self.rate = '+0%'  # Speech rate (-50% to +50%)
        self.pitch = '+0Hz'  # Speech pitch (-50Hz to +50Hz)
        self.volume = '+0%'  # Volume (0% to 100%)
    
    def set_voice(self, voice_name: str):
        """
        Set the TTS voice
        Đặt giọng đọc
        
        Args:
            voice_name: Display name from VIETNAMESE_VOICES
        """
        if voice_name in self.VIETNAMESE_VOICES:
            self.voice = self.VIETNAMESE_VOICES[voice_name]
        else:
            # Assume it's already a voice ID
            self.voice = voice_name
    
    def set_rate(self, rate_percent: int):
        """
        Set speech rate
        Đặt tốc độ đọc
        
        Args:
            rate_percent: -50 to +50
        """
        rate_percent = max(-50, min(50, rate_percent))
        self.rate = f"{rate_percent:+d}%"
    
    def set_pitch(self, pitch_hz: int):
        """
        Set speech pitch
        Đặt cao độ giọng
        
        Args:
            pitch_hz: -50 to +50
        """
        pitch_hz = max(-50, min(50, pitch_hz))
        self.pitch = f"{pitch_hz:+d}Hz"
    
    def set_volume(self, volume_percent: int):
        """
        Set volume level
        Đặt âm lượng
        
        Args:
            volume_percent: 0 to 100
        """
        volume_percent = max(0, min(100, volume_percent))
        # Convert to relative format (0-100 -> -100% to 0%)
        relative_volume = volume_percent - 100
        self.volume = f"{relative_volume:+d}%"
    
    async def generate_audio_with_subtitles(
        self,
        text: str,
        output_audio_path: str,
        output_subtitle_path: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """
        Generate audio file with optional subtitles
        Tạo file audio và phụ đề
        
        Args:
            text: Vietnamese text to convert
            output_audio_path: Path for output MP3 file
            output_subtitle_path: Optional path for SRT subtitle file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with success status and metadata
        """
        try:
            if progress_callback:
                progress_callback(f"🎤 Đang tạo audio: {Path(output_audio_path).name}")
            
            # Create communicate object / Tạo đối tượng communicate
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume
            )
            
            # Create output directory if needed / Tạo thư mục output
            Path(output_audio_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Generate audio and subtitles / Tạo audio và phụ đề
            if output_subtitle_path:
                Path(output_subtitle_path).parent.mkdir(parents=True, exist_ok=True)
                submaker = edge_tts.SubMaker()
                
                with open(output_audio_path, "wb") as audio_file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_file.write(chunk["data"])
                        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                            submaker.feed(chunk)
                
                # Write subtitle file / Ghi file phụ đề
                with open(output_subtitle_path, "w", encoding="utf-8") as sub_file:
                    sub_file.write(submaker.get_srt())
                
                if progress_callback:
                    progress_callback(f"✅ Đã tạo: {Path(output_audio_path).name} + subtitle")
            else:
                # Audio only / Chỉ audio
                await communicate.save(output_audio_path)
                
                if progress_callback:
                    progress_callback(f"✅ Đã tạo: {Path(output_audio_path).name}")
            
            return {
                'success': True,
                'audio_path': output_audio_path,
                'subtitle_path': output_subtitle_path,
                'voice': self.voice,
                'rate': self.rate,
                'pitch': self.pitch
            }
            
        except Exception as e:
            error_msg = f"❌ Lỗi khi tạo audio: {e}"
            if progress_callback:
                progress_callback(error_msg)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_audio_sync(
        self,
        text: str,
        output_audio_path: str,
        output_subtitle_path: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """
        Synchronous wrapper for audio generation
        Wrapper đồng bộ cho việc tạo audio
        
        Args:
            Same as generate_audio_with_subtitles
            
        Returns:
            Result dictionary
        """
        return asyncio.run(
            self.generate_audio_with_subtitles(
                text, output_audio_path, output_subtitle_path, progress_callback
            )
        )
    
    async def get_audio_duration(self, audio_path: str) -> float:
        """
        Get duration of audio file in seconds
        Lấy thời lượng file audio (giây)
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            # Use a simple method - count audio chunks
            # For more precise duration, would need additional library like mutagen
            # For now, return estimated duration based on file size
            
            file_size = Path(audio_path).stat().st_size
            # Rough estimate: 1 second ≈ 16-32 KB at 128kbps
            estimated_duration = file_size / 24000  # Rough middle estimate
            
            return estimated_duration
            
        except Exception as e:
            print(f"⚠️ Không thể lấy thời lượng audio: {e}")
            return 0.0
    
    @staticmethod
    def clean_text_for_tts(text: str) -> str:
        """
        Clean and prepare text for TTS
        Làm sạch và chuẩn bị văn bản cho TTS
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace / Xóa khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        # Keep Vietnamese characters, punctuation, numbers
        text = re.sub(r'[^\w\s\.,;:!?\-–—\"\'()àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]', '', text)
        
        # Trim / Cắt khoảng trắng đầu cuối
        text = text.strip()
        
        return text


# Test the module / Kiểm tra module
if __name__ == "__main__":
    import asyncio
    
    async def test_tts():
        """Test TTS engine"""
        engine = TTSEngine()
        
        # Test Vietnamese text / Kiểm tra văn bản tiếng Việt
        test_text = "Xin chào! Đây là một bài kiểm tra chuyển văn bản tiếng Việt thành giọng nói."
        
        # Set voice and parameters / Đặt giọng và tham số
        engine.set_voice('HoaiMy (Nữ)')
        engine.set_rate(0)
        engine.set_pitch(0)
        engine.set_volume(100)
        
        print("🎤 Bắt đầu chuyển đổi TTS...")
        
        result = await engine.generate_audio_with_subtitles(
            text=test_text,
            output_audio_path="test_output/test_audio.mp3",
            output_subtitle_path="test_output/test_audio.srt",
            progress_callback=lambda msg: print(f"  {msg}")
        )
        
        if result['success']:
            print(f"\n✅ Thành công!")
            print(f"   Audio: {result['audio_path']}")
            print(f"   Subtitle: {result['subtitle_path']}")
            print(f"   Voice: {result['voice']}")
        else:
            print(f"\n❌ Lỗi: {result['error']}")
    
    # Run test
    asyncio.run(test_tts())
