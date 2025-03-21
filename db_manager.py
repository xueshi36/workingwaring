"""
数据库管理模块 - 处理活动数据的存储和检索

本模块负责以下任务:
1. 创建和维护SQLite数据库结构
2. 记录用户每分钟的活动数据
3. 提供数据检索和统计功能
4. 汇总每日使用情况

表结构:
- minute_activity: 存储每分钟的详细活动数据
- daily_summary: 存储每日汇总使用统计
"""

import sqlite3
import os
import logging
import threading
from datetime import datetime, timedelta
import sys

class DatabaseManager:
    def __init__(self, db_path="usage_data.db"):
        """初始化数据库管理器
        
        创建数据库连接并确保所需表结构存在。如果数据库文件不存在，
        会自动创建数据库和所需表结构。
        
        参数:
            db_path (str): 数据库文件路径，默认为当前目录下的usage_data.db
        """
        # 获取应用程序目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的EXE
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        # 确保数据存储目录存在
        data_dir = os.path.join(application_path, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 设置数据库路径
        self.db_path = os.path.join(data_dir, db_path)
        logging.info(f"数据库路径: {self.db_path}")
        
        self.local = threading.local()  # 创建线程局部存储对象
        
        # 初始化主线程的连接
        self._initialize_db()
        
    def _get_connection(self):
        """获取当前线程的数据库连接
        
        如果当前线程没有连接，则创建一个新连接。
        这确保每个线程使用自己的SQLite连接。
        
        返回:
            tuple: (connection, cursor) 数据库连接和游标对象
        """
        # 检查当前线程是否已有连接
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            # 为当前线程创建新连接
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.cursor = self.local.conn.cursor()
            logging.debug(f"线程 {threading.get_ident()} 创建了新的数据库连接")
        
        return self.local.conn, self.local.cursor
        
    def _initialize_db(self):
        """初始化数据库连接和表结构
        
        检查数据库文件是否存在，创建连接并初始化表结构(如需要)。
        这是一个内部方法，由__init__方法调用。
        """
        # 获取当前线程的连接
        conn, cursor = self._get_connection()
        
        try:
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='minute_activity'")
            table_exists = cursor.fetchone() is not None
            
            # 如果表不存在，创建表结构
            if not table_exists:
                logging.info("数据库表不存在，正在创建表结构...")
                self._create_tables(conn, cursor)
            else:
                logging.info("数据库表已存在")
        
        except Exception as e:
            logging.error(f"检查数据库表结构时出错: {e}")
            # 如果发生错误，尝试创建表
            try:
                self._create_tables(conn, cursor)
            except Exception as create_error:
                logging.error(f"创建数据库表结构失败: {create_error}")
        
        logging.info(f"数据库初始化完成: {self.db_path}")
        
    def _create_tables(self, conn, cursor):
        """创建数据库表结构
        
        创建两个主要表:
        1. minute_activity: 记录每分钟的活动详情
        2. daily_summary: 记录每日使用汇总数据
        
        参数:
            conn: 数据库连接
            cursor: 数据库游标
        """
        # 创建分钟活动记录表 - 存储每分钟的详细活动数据
        cursor.execute('''
        CREATE TABLE minute_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 自增主键
            timestamp TEXT NOT NULL,               -- 时间戳(YYYY-MM-DD HH:MM:SS格式)
            date TEXT NOT NULL,                    -- 日期部分(YYYY-MM-DD格式)
            time TEXT NOT NULL,                    -- 时间部分(HH:MM:SS格式)
            is_active INTEGER NOT NULL,            -- 是否活跃(1=活跃,0=不活跃)
            mouse_moves INTEGER NOT NULL,          -- 鼠标移动次数
            key_presses INTEGER NOT NULL           -- 按键次数
        )
        ''')
        
        # 创建每日汇总数据表 - 存储每日使用统计
        cursor.execute('''
        CREATE TABLE daily_summary (
            date TEXT PRIMARY KEY,                 -- 日期(YYYY-MM-DD格式)
            total_active_minutes INTEGER NOT NULL, -- 当日总活跃分钟数
            longest_session INTEGER NOT NULL,      -- 最长连续使用会话(分钟)
            last_updated TEXT NOT NULL             -- 最后更新时间
        )
        ''')
        
        conn.commit()
        logging.info("数据库表结构创建完成")
        
    def record_minute_activity(self, timestamp, is_active, mouse_moves, key_presses):
        """记录每分钟活动数据
        
        将当前分钟的活动信息保存到数据库，并更新每日汇总。
        
        参数:
            timestamp (datetime): 记录时间
            is_active (bool): 该分钟是否有活动
            mouse_moves (int): 鼠标移动次数
            key_presses (int): 按键次数
            
        返回:
            bool: 操作是否成功
        """
        # 获取当前线程的连接
        conn, cursor = self._get_connection()
        
        # 格式化日期和时间
        date_str = timestamp.strftime("%Y-%m-%d")  # 提取日期部分
        time_str = timestamp.strftime("%H:%M:%S")  # 提取时间部分
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")  # 完整时间戳
        
        try:
            # 插入活动记录
            cursor.execute(
                "INSERT INTO minute_activity (timestamp, date, time, is_active, mouse_moves, key_presses) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp_str, date_str, time_str, 1 if is_active else 0, mouse_moves, key_presses)
            )
            conn.commit()
            
            # 更新每日汇总数据
            self._update_daily_summary(date_str)
            
            return True
        except Exception as e:
            logging.error(f"记录活动数据失败: {e}")
            try:
                conn.rollback()  # 发生错误时回滚事务
            except Exception as rollback_error:
                logging.error(f"回滚事务失败: {rollback_error}")
            return False
            
    def update_daily_summary(self, date_str, total_minutes=None):
        """更新每日汇总数据
        
        计算并更新指定日期的使用统计数据，包括总活跃分钟数和最长连续会话。
        
        参数:
            date_str (str): 日期字符串 (YYYY-MM-DD)
            total_minutes (int, optional): 如果提供，直接使用此值作为总使用分钟数
        """
        if total_minutes is not None:
            # 如果提供了total_minutes参数，直接更新数据库
            conn, cursor = self._get_connection()
            try:
                # 获取最长会话 - 这个我们仍然需要计算
                cursor.execute("""
                    SELECT COUNT(*) AS session_length
                    FROM (
                        SELECT 
                            id,
                            timestamp,
                            is_active,
                            (
                                SELECT COUNT(*) 
                                FROM minute_activity AS m2 
                                WHERE m2.is_active = 0 AND m2.timestamp <= m1.timestamp
                                AND m2.date = ?
                            ) AS reset_group
                        FROM minute_activity AS m1
                        WHERE m1.date = ?
                        AND m1.is_active = 1
                    ) AS active_with_reset
                    GROUP BY reset_group
                    ORDER BY session_length DESC
                    LIMIT 1
                """, (date_str, date_str))
                
                result = cursor.fetchone()
                longest_session = result[0] if result else 0
                
                # 更新或插入每日汇总记录
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_summary 
                    (date, total_active_minutes, longest_session, last_updated)
                    VALUES (?, ?, ?, ?)
                """, (date_str, total_minutes, longest_session, now))
                
                conn.commit()
            except Exception as e:
                logging.error(f"使用提供的总分钟数更新每日汇总失败: {e}")
                try:
                    conn.rollback()
                except Exception as rollback_err:
                    logging.error(f"回滚事务失败: {rollback_err}")
        else:
            # 否则使用内部方法计算并更新
            self._update_daily_summary(date_str)
        
    def _update_daily_summary(self, date_str):
        """更新每日汇总数据
        
        计算并更新指定日期的使用统计数据，包括总活跃分钟数和最长连续会话。
        这是一个内部方法，在每次记录分钟活动后调用。
        
        参数:
            date_str (str): 日期字符串 (YYYY-MM-DD)
        """
        # 获取当前线程的连接
        conn, cursor = self._get_connection()
        
        try:
            # 获取当日活跃分钟总数 - 计算is_active=1的记录数
            cursor.execute(
                "SELECT COUNT(*) FROM minute_activity WHERE date = ? AND is_active = 1",
                (date_str,)
            )
            active_minutes = cursor.fetchone()[0]
            
            # 计算最长会话 - 这是一个复杂查询，找出连续活跃记录的最长序列
            cursor.execute("""
                SELECT COUNT(*) AS session_length
                FROM (
                    SELECT 
                        id,
                        timestamp,
                        is_active,
                        (
                            SELECT COUNT(*) 
                            FROM minute_activity AS m2 
                            WHERE m2.is_active = 0 AND m2.timestamp <= m1.timestamp
                            AND m2.date = ?
                        ) AS reset_group
                    FROM minute_activity AS m1
                    WHERE m1.date = ?
                    AND m1.is_active = 1
                ) AS active_with_reset
                GROUP BY reset_group
                ORDER BY session_length DESC
                LIMIT 1
            """, (date_str, date_str))
            
            result = cursor.fetchone()
            longest_session = result[0] if result else 0
            
            # 更新或插入每日汇总记录
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR REPLACE INTO daily_summary 
                (date, total_active_minutes, longest_session, last_updated)
                VALUES (?, ?, ?, ?)
            """, (date_str, active_minutes, longest_session, now))
            
            conn.commit()
        except Exception as e:
            logging.error(f"更新每日汇总失败: {e}")
            try:
                conn.rollback()  # 发生错误时回滚事务
            except Exception as rollback_error:
                logging.error(f"回滚事务失败: {rollback_error}")
            
    def get_day_activity(self, date=None):
        """获取指定日期的每小时活动数据
        
        参数:
            date (str, optional): 日期字符串 (YYYY-MM-DD)，默认为今天
            
        返回:
            list: 包含24个元素的列表，每个元素表示对应小时的活跃分钟数
        """
        # 获取当前线程的连接
        conn, cursor = self._get_connection()
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        # 初始化24小时的数据数组
        hourly_data = [0] * 24
        
        try:
            # 按小时分组统计活跃分钟数
            cursor.execute("""
                SELECT strftime('%H', time) AS hour, COUNT(*) 
                FROM minute_activity 
                WHERE date = ? AND is_active = 1
                GROUP BY hour
            """, (date,))
            
            # 填充结果数组
            for row in cursor.fetchall():
                hour = int(row[0])  # 小时(0-23)
                count = row[1]      # 该小时的活跃分钟数
                hourly_data[hour] = count
                
            return hourly_data
        except Exception as e:
            logging.error(f"获取日活动数据失败: {e}")
            return hourly_data  # 返回空数组(全0)
            
    def get_weekly_heatmap_data(self, end_date=None):
        """获取周热力图数据
        
        参数:
            end_date (str/datetime, optional): 结束日期，默认为今天
            
        返回:
            dict: 以日期为键，24小时活跃分钟数列表为值的字典
        """
        # 处理结束日期参数
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            
        # 计算开始日期(往前6天，总共获取7天数据)
        start_date = end_date - timedelta(days=6)
        
        # 初始化结果字典
        result = {}
        current_date = start_date
        
        # 获取每一天的数据
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            # 调用get_day_activity获取该日的小时活动数据
            result[date_str] = self.get_day_activity(date_str)
            current_date += timedelta(days=1)
            
        return result
        
    def get_daily_summaries(self, days=30):
        """获取最近N天的汇总数据
        
        参数:
            days (int): 要检索的天数，默认为30
            
        返回:
            list: 包含(日期,总活跃分钟数,最长会话)元组的列表
        """
        # 获取当前线程的连接
        conn, cursor = self._get_connection()
        
        try:
            # 查询daily_summary表获取最近的记录
            cursor.execute("""
                SELECT date, total_active_minutes, longest_session 
                FROM daily_summary
                ORDER BY date DESC
                LIMIT ?
            """, (days,))
            
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"获取每日汇总失败: {e}")
            return []
            
    def close(self):
        """关闭数据库连接
        
        安全关闭数据库连接，应在程序退出前调用。
        """
        # 关闭当前线程的连接
        if hasattr(self.local, 'conn') and self.local.conn is not None:
            self.local.conn.close()
            self.local.conn = None
            self.local.cursor = None
            logging.info(f"线程 {threading.get_ident()} 的数据库连接已关闭") 