"""
cciic主程序入口
"""

import sys
import threading
from .player import MusicPlayer
from .momo_display import MomoDisplay

def main():
    """主程序入口函数"""
    
    # 创建音乐播放器
    player = MusicPlayer()
    
    # 创建momo显示窗口
    display = MomoDisplay()
    
    # 在后台线程启动音乐播放
    music_thread = threading.Thread(target=player.play_loop, daemon=True)
    music_thread.start()
    
    # 在主线程启动图片显示
    try:
        display.run()
    except KeyboardInterrupt:
        print("\n👋 再见！")
    finally:
        player.stop()
        display.cleanup()

if __name__ == "__main__":
    main()
