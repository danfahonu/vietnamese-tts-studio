#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Player Module for TTS GUI
Module phát audio cho GUI TTS
"""

import pygame
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from enum import Enum


class PlayerState(Enum):
    """Player state enumeration / Trạng thái player"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioPlayer:
    """
    Audio player with play/pause/stop controls
    Trình phát audio với điều khiển play/pause/stop
    """
    
    def __init__(self):
        """Initialize audio player / Khởi tạo player"""
        # Initialize pygame mixer / Khởi tạo pygame mixer
        pygame.mixer.init()
        
        # State variables / Biến trạng thái
        self.state = PlayerState.STOPPED
        self.current_file: Optional[Path] = None
        self.volume = 1.0  # 0.0 to 1.0
        self.duration = 0.0  # Duration in seconds
        self.start_time = 0.0
        self.pause_time = 0.0
        
        # Callbacks / Hàm callback
        self.on_finish_callback: Optional[Callable] = None
        self.on_state_change_callback: Optional[Callable[[PlayerState], None]] = None
        
        # Monitor thread / Thread giám sát
        self.monitor_thread: Optional[threading.Thread] = None
        self.should_monitor = False
    
    def load(self, audio_path: str) -> bool:
        """
        Load audio file
        Tải file audio
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if successful
        """
        try:
            self.stop()
            
            audio_file = Path(audio_path)
            if not audio_file.exists():
                print(f"❌ File không tồn tại: {audio_path}")
                return False
            
            # Load audio / Tải audio
            pygame.mixer.music.load(str(audio_file))
            self.current_file = audio_file
            
            # Get duration (pygame doesn't provide this directly, use estimate)
            # For accurate duration, would need mutagen or other library
            file_size = audio_file.stat().st_size
            self.duration = file_size / 24000  # Rough estimate for MP3
            
            self._update_state(PlayerState.STOPPED)
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi load audio: {e}")
            return False
    
    def play(self) -> bool:
        """
        Play or resume audio
        Phát hoặc tiếp tục audio
        
        Returns:
            True if successful
        """
        try:
            if self.state == PlayerState.PAUSED:
                # Resume / Tiếp tục
                pygame.mixer.music.unpause()
                self._update_state(PlayerState.PLAYING)
            else:
                # Start playing / Bắt đầu phát
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                self.start_time = time.time()
                self._update_state(PlayerState.PLAYING)
                
                # Start monitor thread / Bắt đầu thread giám sát
                self._start_monitor()
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi phát audio: {e}")
            return False
    
    def pause(self) -> bool:
        """
        Pause audio
        Tạm dừng audio
        
        Returns:
            True if successful
        """
        try:
            if self.state == PlayerState.PLAYING:
                pygame.mixer.music.pause()
                self.pause_time = time.time()
                self._update_state(PlayerState.PAUSED)
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi tạm dừng: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop audio
        Dừng audio
        
        Returns:
            True if successful
        """
        try:
            pygame.mixer.music.stop()
            self.unload()  # Unload file to release it
            self._update_state(PlayerState.STOPPED)
            self._stop_monitor()
            self.start_time = 0.0
            self.pause_time = 0.0
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi dừng: {e}")
            return False
    
    def unload(self):
        """
        Unload current audio file to release file handle
        Giải phóng file audio để có thể ghi đè
        """
        try:
            pygame.mixer.music.unload()
            self.current_file = None
        except Exception as e:
            print(f"⚠️ Lỗi khi unload: {e}")
    
    def set_volume(self, volume: float):
        """
        Set playback volume
        Đặt âm lượng phát
        
        Args:
            volume: 0.0 to 1.0
        """
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
    
    def get_position(self) -> float:
        """
        Get current playback position in seconds
        Lấy vị trí phát hiện tại (giây)
        
        Returns:
            Position in seconds
        """
        if self.state == PlayerState.PLAYING:
            # pygame.mixer.music.get_pos() returns milliseconds since start
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return pos_ms / 1000.0
        elif self.state == PlayerState.PAUSED:
            return self.pause_time - self.start_time
        
        return 0.0
    
    def get_progress(self) -> float:
        """
        Get playback progress as percentage
        Lấy tiến trình phát (%)
        
        Returns:
            Progress 0.0 to 1.0
        """
        if self.duration > 0:
            return min(1.0, self.get_position() / self.duration)
        return 0.0
    
    def is_playing(self) -> bool:
        """Check if currently playing / Kiểm tra có đang phát không"""
        return self.state == PlayerState.PLAYING
    
    def set_on_finish_callback(self, callback: Callable):
        """
        Set callback when playback finishes
        Đặt callback khi phát xong
        """
        self.on_finish_callback = callback
    
    def set_on_state_change_callback(self, callback: Callable[[PlayerState], None]):
        """
        Set callback when state changes
        Đặt callback khi trạng thái thay đổi
        """
        self.on_state_change_callback = callback
    
    def _update_state(self, new_state: PlayerState):
        """Update player state / Cập nhật trạng thái"""
        self.state = new_state
        if self.on_state_change_callback:
            self.on_state_change_callback(new_state)
    
    def _start_monitor(self):
        """Start monitoring thread / Bắt đầu thread giám sát"""
        self.should_monitor = True
        self.monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self.monitor_thread.start()
    
    def _stop_monitor(self):
        """Stop monitoring thread / Dừng thread giám sát"""
        self.should_monitor = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_playback(self):
        """
        Monitor playback and detect when it finishes
        Giám sát phát và phát hiện khi kết thúc
        """
        while self.should_monitor:
            time.sleep(0.1)  # Check every 100ms
            
            if self.state == PlayerState.PLAYING:
                # Check if music has stopped (finished)
                if not pygame.mixer.music.get_busy():
                    self._update_state(PlayerState.STOPPED)
                    if self.on_finish_callback:
                        self.on_finish_callback()
                    break
    
    def cleanup(self):
        """
        Cleanup resources
        Dọn dẹp tài nguyên
        """
        self.stop()
        pygame.mixer.quit()


# Test the module / Kiểm tra module
if __name__ == "__main__":
    def on_finish():
        print("✅ Phát xong!")
    
    def on_state_change(state: PlayerState):
        print(f"🔄 Trạng thái: {state.value}")
    
    # This is just a test example
    # Đây chỉ là ví dụ test
    player = AudioPlayer()
    player.set_on_finish_callback(on_finish)
    player.set_on_state_change_callback(on_state_change)
    
    print("AudioPlayer module loaded successfully!")
    print("Sử dụng trong GUI để phát audio preview.")
