"""
momo图片弹跳显示模块
使用tkinter和PIL显示gif图片并实现弹跳效果
"""

import tkinter as tk
from tkinter import messagebox
import random
import time
import threading
from pathlib import Path
from PIL import Image, ImageTk, ImageSequence

class MomoDisplay:
    """momo图片弹跳显示类"""
    
    def __init__(self):
        """初始化显示窗口"""
        self.root = None
        self.canvas = None
        self.image_label = None
        self.current_image = None
        self.current_gif = None
        self.current_gif_frames = []
        self.current_frame_index = 0
        self.image_files = []
        self.current_image_index = 0
        
        # 弹跳参数
        self.x = 100
        self.y = 100
        self.dx = random.randint(2, 5) * random.choice([-1, 1])  # x方向速度
        self.dy = random.randint(2, 5) * random.choice([-1, 1])  # y方向速度
        
        # 窗口参数
        self.window_width = 0
        self.window_height = 0
        
        # 控制参数
        self.running = False
        self.image_switch_interval = 30  # 30秒切换一次图片
        self.last_switch_time = time.time()
        self.gif_frame_interval = 0.1  # GIF帧间隔（秒）
        self.last_frame_time = time.time()
        
        # 准备图片文件列表
        self.image_files = []
        self._load_images()
    
    def _load_images(self):
        """加载所有gif图片"""
        images_dir = Path(__file__).parent / "assets" / "images"
        image_files = list(images_dir.glob("*.gif"))
        
        if not image_files:
            print("❌ 未找到momo图片文件")
            return
        
        print(f"📸 找到 {len(image_files)} 张momo图片")
        
        # 只保存图片路径，不立即创建PhotoImage
        self.image_files = image_files
        print(f"✅ 准备加载 {len(self.image_files)} 张GIF")
    
    def _load_gif_frames(self, gif_path):
        """加载GIF的所有帧"""
        try:
            gif = Image.open(gif_path)
            self.current_gif_frames = []
            self.current_frame_index = 0
            
            # 提取所有帧
            for frame in ImageSequence.Iterator(gif):
                # 确保帧有透明通道
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')
                # 转换为PhotoImage
                photo = ImageTk.PhotoImage(frame)
                self.current_gif_frames.append(photo)
            
            print(f"✅ 成功提取 {len(self.current_gif_frames)} 帧")
        except Exception as e:
            print(f"❌ 加载GIF帧失败: {e}")
            self.current_gif_frames = []
    
    def _update_gif_frame(self):
        """更新GIF帧"""
        if not self.current_gif_frames or len(self.current_gif_frames) <= 1:
            return
        
        current_time = time.time()
        if current_time - self.last_frame_time >= self.gif_frame_interval:
            # 切换到下一帧
            self.current_frame_index = (self.current_frame_index + 1) % len(self.current_gif_frames)
            self.current_image = self.current_gif_frames[self.current_frame_index]
            
            # 更新画布中的图片
            if self.canvas and self.image_label:
                self.canvas.itemconfig(self.image_label, image=self.current_image)
            
            self.last_frame_time = current_time
    
    def _create_window(self):
        """创建显示窗口"""
        self.root = tk.Tk()
        self.root.title("耄耋momo")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 先加载第一张GIF来获取窗口大小
        if self.image_files:
            try:
                # 加载GIF文件并提取所有帧
                self._load_gif_frames(self.image_files[0])
                if self.current_gif_frames:
                    self.current_image = self.current_gif_frames[0]
                    self.window_width = self.current_image.width()
                    self.window_height = self.current_image.height()
                    print(f"✅ 成功加载第一张GIF: {self.image_files[0].name} ({len(self.current_gif_frames)}帧)")
                else:
                    raise Exception("无法提取GIF帧")
            except Exception as e:
                print(f"❌ 加载第一张GIF失败: {e}")
                self.window_width = 200
                self.window_height = 200
                self.current_image = None
                self.current_gif_frames = []
        else:
            self.window_width = 200
            self.window_height = 200
            self.current_image = None
            self.current_gif_frames = []
        
        # 设置窗口位置（随机初始位置）
        self.x = random.randint(0, screen_width - self.window_width)
        self.y = random.randint(0, screen_height - self.window_height)
        
        # 配置窗口
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x}+{self.y}")
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-topmost', True)  # 置顶
        self.root.attributes('-alpha', 0.9)  # 半透明
        self.root.configure(bg='white')  # 设置窗口背景为白色
        
        # 创建画布，设置透明背景
        self.canvas = tk.Canvas(
            self.root, 
            width=self.window_width, 
            height=self.window_height,
            highlightthickness=0,
            bg='white'
        )
        self.canvas.pack()
        
        # 创建图片标签
        if self.current_image:
            self.image_label = self.canvas.create_image(
                self.window_width // 2, 
                self.window_height // 2, 
                image=self.current_image
            )
        else:
            self.image_label = None
        
        # 绑定事件
        self.root.bind('<Escape>', self._on_escape)
        self.root.bind('<Button-3>', self._on_right_click)  # 右键退出
        self.root.bind('<Button-1>', self._on_left_click)   # 左键切换图片
        
        print("🖼️ momo窗口创建完成")
    
    def _on_escape(self, event):
        """ESC键退出"""
        self.stop()
    
    def _on_right_click(self, event):
        """右键退出"""
        self.stop()
    
    def _on_left_click(self, event):
        """左键切换图片"""
        self._switch_image()
    
    def _switch_image(self):
        """切换GIF"""
        if len(self.image_files) <= 1:
            return
        
        self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
        
        try:
            # 加载新GIF的所有帧
            self._load_gif_frames(self.image_files[self.current_image_index])
            if self.current_gif_frames:
                self.current_image = self.current_gif_frames[0]
                self.current_frame_index = 0
                
                # 更新画布中的图片
                if self.canvas and self.image_label:
                    self.canvas.itemconfig(self.image_label, image=self.current_image)
                
                print(f"🔄 切换到GIF {self.current_image_index + 1}/{len(self.image_files)}: {self.image_files[self.current_image_index].name} ({len(self.current_gif_frames)}帧)")
            else:
                print(f"❌ 无法加载GIF帧: {self.image_files[self.current_image_index].name}")
        except Exception as e:
            print(f"❌ 切换GIF失败: {e}")
    
    def _update_position(self):
        """更新图片位置（弹跳逻辑）"""
        if not self.root or not self.running:
            return
        
        # 更新位置
        self.x += self.dx
        self.y += self.dy
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 边界检测和反弹
        if self.x <= 0 or self.x >= screen_width - self.window_width:
            self.dx = -self.dx
            self.x = max(0, min(self.x, screen_width - self.window_width))
        
        if self.y <= 0 or self.y >= screen_height - self.window_height:
            self.dy = -self.dy
            self.y = max(0, min(self.y, screen_height - self.window_height))
        
        # 更新窗口位置
        self.root.geometry(f"{self.window_width}x{self.window_height}+{int(self.x)}+{int(self.y)}")
    
    def _animation_loop(self):
        """动画循环"""
        while self.running:
            try:
                # 更新位置
                self._update_position()
                
                # 更新GIF帧
                self._update_gif_frame()
                
                # 检查是否需要切换图片
                current_time = time.time()
                if current_time - self.last_switch_time >= self.image_switch_interval:
                    self._switch_image()
                    self.last_switch_time = current_time
                
                # 更新窗口
                if self.root:
                    self.root.update()
                
                time.sleep(0.016)  # 约60FPS
                
            except tk.TclError:
                # 窗口被关闭
                break
            except Exception as e:
                print(f"❌ 动画循环出错: {e}")
                break
    
    def run(self):
        """运行显示程序"""
        if not self.image_files:
            print("❌ 没有可显示的图片")
            return
        
        self._create_window()
        self.running = True
        
        # 启动动画线程
        animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        animation_thread.start()
        
        print("🎯 momo开始弹跳！")
        
        # 主循环
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"❌ 窗口运行出错: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """停止显示"""
        self.running = False
        if self.root:
            self.root.quit()
            self.root.destroy()
        print("👋 momo显示已停止")
    
    def cleanup(self):
        """清理资源"""
        self.stop()
