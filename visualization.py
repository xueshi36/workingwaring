"""
数据可视化模块 - 生成使用数据的可视化报表

本模块负责:
1. 生成每日使用情况图表
2. 创建周活动热力图
3. 生成月度使用统计报告
4. 生成包含所有报表的HTML页面
"""

import os
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import log_manager

class UsageVisualizer:
    def __init__(self, db_manager, output_dir="reports"):
        """初始化可视化器
        
        参数:
            db_manager: 数据库管理器实例
            output_dir: 输出报告的目录
        """
        self.db_manager = db_manager
        self.output_dir = output_dir
        
        # 确保输出目录存在
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                log_manager.info(f"可视化器创建输出目录: {output_dir}")
        except Exception as e:
            log_manager.error(f"创建报告目录失败: {e}")
            # 尝试使用相对路径
            if not os.path.isabs(output_dir):
                alt_dir = os.path.abspath(output_dir)
                try:
                    os.makedirs(alt_dir, exist_ok=True)
                    self.output_dir = alt_dir
                    log_manager.info(f"改用绝对路径创建输出目录: {alt_dir}")
                except Exception as e2:
                    log_manager.error(f"创建绝对路径报告目录也失败: {e2}")
            
        # 设置中文字体支持
        self._setup_fonts()
            
        log_manager.info(f"可视化系统初始化，输出目录: {self.output_dir}")
        
    def _setup_fonts(self):
        """设置支持中文的字体"""
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            log_manager.info("字体设置完成，支持中文显示")
        except Exception as e:
            log_manager.warning(f"设置中文字体失败: {e}")
        
    def generate_daily_report(self, date=None):
        """生成每日使用报告
        
        参数:
            date: 要生成报告的日期 (YYYY-MM-DD)，默认为今天
        
        返回:
            str: 生成的报告文件路径
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        log_manager.info(f"开始生成{date}的每日使用报告...")
        hourly_data = self.db_manager.get_day_activity(date)
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # X轴为小时 (0-23)
        hours = list(range(24))
        
        # 绘制柱状图
        bars = ax.bar(hours, hourly_data, color='#3498db', alpha=0.7, width=0.7)
        
        # 在柱子上方添加数值
        for bar, count in zip(bars, hourly_data):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                       str(count), ha='center', va='bottom')
        
        # 设置图表标题和标签
        ax.set_title(f"每小时电脑使用情况 ({date})", fontsize=14)
        ax.set_xlabel("小时", fontsize=12)
        ax.set_ylabel("活跃分钟数", fontsize=12)
        
        # 设置X轴刻度
        ax.set_xticks(hours)
        ax.set_xticklabels([f"{h:02d}:00" for h in hours], rotation=45)
        
        # 设置Y轴最大值
        max_minutes = max(hourly_data) if max(hourly_data) > 0 else 10
        ax.set_ylim(0, max_minutes + 5)
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 紧凑布局
        plt.tight_layout()
        
        # 保存图像
        filename = f"daily_report_{date}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=120)
        plt.close(fig)
        
        log_manager.info(f"生成每日报告图表: {filepath}")
        return filepath
        
    def generate_weekly_heatmap(self, end_date=None):
        """生成周热力图
        
        参数:
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天
        
        返回:
            str: 生成的热力图文件路径
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        log_manager.info(f"开始生成截至{end_date}的周热力图...")
        # 获取一周的数据
        weekly_data = self.db_manager.get_weekly_heatmap_data(end_date)
        
        # 准备热力图数据
        dates = list(weekly_data.keys())
        dates.sort()  # 确保日期有序
        
        # 记录数据情况
        if len(dates) == 0:
            log_manager.warning("没有找到周数据，热力图可能为空")
        else:
            log_manager.info(f"获取到{len(dates)}天的数据，从{dates[0]}到{dates[-1]}")
            
        # 创建数据矩阵
        data_matrix = []
        for date in dates:
            data_matrix.append(weekly_data[date])
            
        # 创建热力图
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 自定义颜色映射
        cmap = LinearSegmentedColormap.from_list('usage_cmap', ['#f7fbff', '#08306b'])
        
        # 绘制热力图
        im = ax.imshow(data_matrix, cmap=cmap, aspect='auto')
        
        # 设置坐标轴
        ax.set_xticks(np.arange(24))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45)
        
        ax.set_yticks(np.arange(len(dates)))
        
        # 格式化日期显示
        date_labels = []
        for date_str in dates:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]
            date_labels.append(f"{date_str} ({weekday})")
            
        ax.set_yticklabels(date_labels)
        
        # 添加颜色条
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('活跃分钟数')
        
        # 在每个单元格上显示值
        for i in range(len(dates)):
            for j in range(24):
                value = data_matrix[i][j]
                if value > 0:
                    text_color = 'white' if value > 30 else 'black'
                    ax.text(j, i, str(value), ha="center", va="center", color=text_color)
        
        # 设置标题
        start_date = dates[0] if dates else "无数据"
        plt.title(f"一周电脑使用热力图 ({start_date} 至 {end_date})", fontsize=14)
        plt.xlabel("小时", fontsize=12)
        
        # 紧凑布局
        plt.tight_layout()
        
        # 保存图像
        filename = f"weekly_heatmap_{start_date}_to_{end_date}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=120)
        plt.close(fig)
        
        log_manager.info(f"生成周热力图: {filepath}")
        return filepath
        
    def generate_monthly_summary(self, days=30):
        """生成月度使用摘要
        
        参数:
            days: 要包含的天数，默认为30天
            
        返回:
            str: 生成的报告文件路径
        """
        log_manager.info(f"开始生成过去{days}天的月度摘要...")
        # 获取每日汇总数据
        daily_data = self.db_manager.get_daily_summaries(days)
        
        if not daily_data:
            log_manager.warning("没有足够的数据生成月度摘要")
            return None
            
        log_manager.info(f"获取到{len(daily_data)}天的数据进行月度摘要")
            
        # 准备绘图数据
        dates = []
        active_minutes = []
        longest_sessions = []
        
        for data in daily_data:
            dates.append(data[0])
            active_minutes.append(data[1])
            longest_sessions.append(data[2])
            
        # 反转列表以便按时间先后顺序显示
        dates.reverse()
        active_minutes.reverse()
        longest_sessions.reverse()
        
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        # 绘制活跃分钟数
        ax1.plot(dates, active_minutes, marker='o', linestyle='-', color='#2980b9', linewidth=2)
        ax1.set_title("每日电脑使用总时间", fontsize=14)
        ax1.set_ylabel("活跃分钟数", fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # 在数据点上显示值
        for i, v in enumerate(active_minutes):
            if i % 3 == 0:  # 每隔几个点显示一次，避免拥挤
                ax1.text(i, v + 5, str(v), ha='center')
        
        # 绘制最长会话
        ax2.plot(dates, longest_sessions, marker='s', linestyle='-', color='#27ae60', linewidth=2)
        ax2.set_title("每日最长连续使用时间", fontsize=14)
        ax2.set_ylabel("连续分钟数", fontsize=12)
        ax2.set_xlabel("日期", fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # 在数据点上显示值
        for i, v in enumerate(longest_sessions):
            if i % 3 == 0:
                ax2.text(i, v + 2, str(v), ha='center')
        
        # 设置x轴日期格式
        if len(dates) > 10:
            # 如果日期太多，只显示部分
            step = len(dates) // 10
            ax2.set_xticks(range(0, len(dates), step))
            ax2.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45)
        else:
            ax2.set_xticks(range(len(dates)))
            ax2.set_xticklabels(dates, rotation=45)
            
        # 紧凑布局
        plt.tight_layout()
        
        # 保存图像
        end_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"monthly_summary_{end_date}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=120)
        plt.close(fig)
        
        log_manager.info(f"生成月度摘要: {filepath}")
        return filepath

    def generate_usage_stats_html(self):
        """生成包含所有报表的HTML页面
        
        返回:
            str: 生成的HTML文件路径
        """
        log_manager.info("开始生成综合使用统计HTML报告...")
        
        # 确保目录存在
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
                log_manager.info(f"创建报告输出目录: {self.output_dir}")
        except Exception as e:
            log_manager.error(f"确保报告目录存在时出错: {e}")
            # 尝试使用当前目录
            self.output_dir = "."
            log_manager.info("改用当前目录作为输出目录")
        
        # 生成所有报表
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            log_manager.info("正在生成每日报告...")
            daily_report = self.generate_daily_report()
            
            log_manager.info("正在生成周热力图...")
            weekly_heatmap = self.generate_weekly_heatmap()
            
            log_manager.info("正在生成月度摘要...")
            monthly_summary = self.generate_monthly_summary()
            
            log_manager.info("所有图表生成完成，开始组装HTML报告...")
            
            # 确保所有报表都生成成功
            if not daily_report or not weekly_heatmap or not monthly_summary:
                log_manager.warning("部分报表生成失败，HTML报告可能不完整")
            
            # 准备HTML内容
            generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>电脑使用时间统计报告</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f7fa;
                        color: #333;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    }}
                    h1, h2 {{
                        color: #2c3e50;
                        border-bottom: 1px solid #eee;
                        padding-bottom: 10px;
                    }}
                    .report-section {{
                        margin: 30px 0;
                    }}
                    .report-image {{
                        width: 100%;
                        max-width: 1100px;
                        height: auto;
                        margin: 15px 0;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }}
                    .footer {{
                        margin-top: 30px;
                        text-align: center;
                        color: #7f8c8d;
                        font-size: 0.9em;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>电脑使用时间统计报告</h1>
                    <p>生成时间: {generation_time}</p>
                    
                    <div class="report-section">
                        <h2>今日使用情况</h2>
                        <img src="{os.path.basename(daily_report)}" alt="每日使用报告" class="report-image">
                        <p>此图表显示了今天每小时的电脑活跃使用分钟数。</p>
                    </div>
                    
                    <div class="report-section">
                        <h2>一周使用热力图</h2>
                        <img src="{os.path.basename(weekly_heatmap)}" alt="周热力图" class="report-image">
                        <p>热力图显示了过去一周每小时的使用情况，颜色越深表示使用时间越长。</p>
                    </div>
                    
                    <div class="report-section">
                        <h2>月度使用摘要</h2>
                        <img src="{os.path.basename(monthly_summary)}" alt="月度摘要" class="report-image">
                        <p>上图显示过去30天的每日总使用时间，下图显示每日最长连续使用会话。</p>
                    </div>
                    
                    <div class="footer">
                        <p>电脑使用时间监控工具 &copy; {datetime.now().year}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 保存HTML文件
            filename = f"usage_report_{today}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                log_manager.log_report_generation(filepath)
                return filepath
            except Exception as e:
                log_manager.error(f"保存HTML报告文件失败: {e}")
                # 尝试使用绝对路径
                try:
                    alt_path = os.path.abspath(os.path.join(".", filename))
                    with open(alt_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    log_manager.info(f"使用替代路径保存HTML报告: {alt_path}")
                    return alt_path
                except Exception as e2:
                    log_manager.error(f"使用替代路径保存HTML也失败: {e2}")
                    raise
                
        except Exception as e:
            log_manager.log_error_detail("报告生成", f"生成HTML报告过程中出错: {e}")
            raise  # 重新抛出异常，让调用者处理 