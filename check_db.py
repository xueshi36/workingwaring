import sqlite3
import datetime

# 连接数据库
conn = sqlite3.connect('data/usage_data.db')
cursor = conn.cursor()

# 检查数据库表结构
print("数据库表结构:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"数据库中有 {len(tables)} 个表: {', '.join([t[0] for t in tables])}")

# 获取daily_summary表结构
print("\n每日汇总表结构:")
try:
    cursor.execute("PRAGMA table_info(daily_summary)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
except Exception as e:
    print(f"获取表结构时出错: {e}")

# 获取最近的活动记录
print("\n最近的活动记录:")
cursor.execute("SELECT timestamp, is_active, mouse_moves, key_presses FROM minute_activity ORDER BY timestamp DESC LIMIT 10")
for row in cursor.fetchall():
    timestamp = row[0]
    is_active = "活跃" if row[1] else "非活跃"
    mouse = row[2]
    keys = row[3]
    print(f"{timestamp} - {is_active}, 鼠标移动: {mouse}, 按键次数: {keys}")

# 获取今日的使用统计
today = datetime.datetime.now().strftime("%Y-%m-%d")
print(f"\n今日({today})使用统计:")
try:
    cursor.execute("SELECT * FROM daily_summary WHERE date = ?", (today,))
    row = cursor.fetchone()
    if row:
        # 获取列名
        cursor.execute("PRAGMA table_info(daily_summary)")
        columns = [col[1] for col in cursor.fetchall()]
        # 打印每一列的值
        for i, value in enumerate(row):
            if i < len(columns):
                print(f"{columns[i]}: {value}")
            else:
                print(f"列{i}: {value}")
    else:
        print(f"今日({today})还没有使用统计记录")
except Exception as e:
    print(f"查询每日汇总时出错: {e}")

# 关闭连接
conn.close() 