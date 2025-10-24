"""
音乐播放模块
使用pygame播放哈基米音乐
"""

import os
import pygame
import threading
import time
from pathlib import Path

class MusicPlayer:
    """音乐播放器类"""
    
    def __init__(self):
        """初始化音乐播放器"""
        # 获取资源文件路径
        self.assets_dir = Path(__file__).parent / "assets" / "music"
        self.music_file = None
        self.is_playing = False
        self.stop_flag = False
        
        # 初始化pygame mixer
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        # 确保音频设备已打开
        if not pygame.mixer.get_init():
            print("❌ 音频设备初始化失败")
        else:
            print("✅ 音频设备初始化成功")
        
        # 查找音乐文件
        self._find_music_file()
    
    def _find_music_file(self):
        """查找音乐文件"""
        music_files = list(self.assets_dir.glob("*.mp3"))
        if music_files:
            self.music_file = music_files[0]
            print(f"🎵 找到音乐文件: {self.music_file.name}")
        else:
            print("❌ 未找到音乐文件")
    
    def play_loop(self):
        """循环播放音乐"""
        if not self.music_file or not self.music_file.exists():
            print("❌ 音乐文件不存在，无法播放")
            return
        
        self.is_playing = True
        self.stop_flag = False
        
        try:
            while not self.stop_flag:
                print("🎵 开始播放哈基米音乐...")
                pygame.mixer.music.load(str(self.music_file))
                pygame.mixer.music.play()
                
                # 等待音乐播放完成或停止信号
                while pygame.mixer.music.get_busy() and not self.stop_flag:
                    time.sleep(0.1)
                
                if not self.stop_flag:
                    print("🔄 音乐播放完成，准备重新播放...")
                    time.sleep(1)  # 短暂停顿后重新播放
                    
        except Exception as e:
            print(f"❌ 音乐播放出错: {e}")
        finally:
            self.is_playing = False
            print("🔇 音乐播放已停止")
    
    def stop(self):
        """停止音乐播放"""
        self.stop_flag = True
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.quit()
    
    def pause(self):
        """暂停音乐"""
        if self.is_playing:
            pygame.mixer.music.pause()
    
    def unpause(self):
        """恢复音乐"""
        if self.is_playing:
            pygame.mixer.music.unpause()
