import pandas as pd
import json

filename = 'MTA_Subway_Hourly_Ridership__Beginning_2025_20260401.csv'

print(f"1. 正在读取文件: {filename} ...")
df = pd.read_csv(filename)
print(f"   成功读取！总行数: {len(df)}")

# 1. 提取日期并筛选 2026年2月4日 的数据
target_date = '02/04/2026'
df_wed = df[df['transit_timestamp'].astype(str).str.startswith(target_date)].copy()
print(f"2. 成功筛选出 {target_date} 的数据！剩余行数: {len(df_wed)}")

# 2. 提取小时 (0-23)
df_wed['hour'] = pd.to_datetime(df_wed['transit_timestamp']).dt.hour

# 3. 清理 ridership 列
df_wed['ridership'] = df_wed['ridership'].astype(str).str.replace(',', '').astype(int)

# 4. 按站点、小时、【支付方式】进行分组聚合
print("3. 正在按站点、小时和支付方式聚合数据...")
grouped = df_wed.groupby(
    ['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour', 'payment_method']
)['ridership'].sum().reset_index()

# 5. 透视表：把 payment_method 展开为 omny 和 metrocard 两列
pivot_df = grouped.pivot_table(
    index=['station_complex_id', 'station_complex', 'latitude', 'longitude', 'hour'],
    columns='payment_method',
    values='ridership',
    fill_value=0
).reset_index()

# 计算该小时总进站人数
pivot_df['in_flow'] = pivot_df.get('omny', 0) + pivot_df.get('metrocard', 0)

# 6. 构建 D3 友好的嵌套 JSON
print("4. 正在生成 JSON 结构...")
output = {}
for h in range(24):
    hour_data = pivot_df[pivot_df['hour'] == h]
    nodes = []
    for _, row in hour_data.iterrows():
         nodes.append({
             "id": str(row['station_complex_id']),
             "name": row['station_complex'],
             "lat": float(row['latitude']),
             "lon": float(row['longitude']),
             "in_flow": int(row['in_flow']),
             "omny": int(row.get('omny', 0)),
             "metrocard": int(row.get('metrocard', 0))
         })
    output[str(h)] = nodes

# 7. 导出最终的 JSON 文件
output_filename = 'subway_day.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

print(f"5. 处理完成！已成功生成 {output_filename}。")