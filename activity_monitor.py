"""
活动监控模块 - 负责检测鼠标和键盘活动
"""

import threading
import time
from pynput import mouse, keyboard
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ActivityMonitor:
    def __init__(self):
        """初始化活动监控器"""
        self.mouse_position = None
        self.last_mouse_position = None
        self.key_press_count = 0
        self.mouse_move_count = 0  # 新增鼠标移动计数
        self.last_activity_time = time.time()
        self.is_active_minute = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        """启动监控线程"""
        if self.running:
            return
            
        self.running = True
        
        # 启动鼠标监听
        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
        self.mouse_listener.start()
        
        # 启动键盘监听
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()
        
        logging.info("活动监控已启动")
    
    def stop(self):
        """停止监控线程"""
        self.running = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        logging.info("活动监控已停止")
    
    def _on_mouse_move(self, x, y):
        """鼠标移动时触发"""
        with self.lock:
            self.mouse_position = (x, y)
            self.mouse_move_count += 1  # 增加移动计数
            self.last_activity_time = time.time()
    
    def _on_key_press(self, key):
        """键盘按键时触发"""
        with self.lock:
            self.key_press_count += 1
            self.last_activity_time = time.time()
    
    def check_activity_minute(self):
        """检查过去一分钟内是否有活动"""
        with self.lock:
            current_position = self.mouse_position
            mouse_moved = (self.last_mouse_position != current_position and 
                          self.last_mouse_position is not None and 
                          current_position is not None)
            
            moves_count = self.mouse_move_count
            keys_count = self.key_press_count
            
            # 更新上次位置并重置按键计数
            self.last_mouse_position = current_position
            
            # 检查是否活跃
            active = mouse_moved or keys_count > 0
            self.is_active_minute = active
            
            # 获取当前状态并重置计数器
            result = {
                "is_active": active,
                "mouse_moves": moves_count,
                "key_presses": keys_count
            }
            
            self.mouse_move_count = 0
            self.key_press_count = 0
            
            if active:
                logging.debug(f"检测到活动: 鼠标移动={mouse_moved}({moves_count}次), 按键次数={keys_count}")
            
            return result
    
    def get_idle_time(self):
        """获取自上次活动以来的时间（秒）"""
        with self.lock:
            return time.time() - self.last_activity_time
    
    def reset(self):
        """重置监控状态"""
        with self.lock:
            self.key_press_count = 0
            self.mouse_move_count = 0
            self.last_mouse_position = None
            self.is_active_minute = False 