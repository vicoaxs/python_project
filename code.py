import re
import pandas as pd
import numpy as np
import json

# 定义用于从日志行中提取信息的正则表达式模式
pattern = re.compile(r'static_multistream\|frame_id:(\d+)\|timestamp:-1\|cpu:(\d+)\|Process(A|B):(start|end):(\d+)')

# 初始化存储解析数据的字典
data = {
    'frame_id': [],
    'cpu': [],
    'process': [],
    'event': [],
    'timestamp': []
}

# 读取日志文件并过滤出包含 "static_multistream" 的行
file_path = r'C:\Users\Vicotiena\Desktop\python_project\trace_analysis.log'
with open(file_path, 'r') as file:
    log_contents = file.readlines()

filtered_lines = [line for line in log_contents if "static_multistream" in line]

# 解析日志行并提取信息
for line in filtered_lines:
    match = pattern.search(line)
    if match:
        data['frame_id'].append(int(match.group(1)))
        data['cpu'].append(int(match.group(2)))
        data['process'].append(f'Process{match.group(3)}')
        data['event'].append(match.group(4))
        data['timestamp'].append(int(match.group(5)))

# 转换为DataFrame以便进一步处理
df = pd.DataFrame(data)

# 计算各工序的耗时
process_durations = {
    'frame_id': [],
    'process': [],
    'duration': []
}

# 遍历唯一的frame_id和process组合，计算其耗时
for frame_id in df['frame_id'].unique():
    for process in ['ProcessA', 'ProcessB']:
        start_time = df[(df['frame_id'] == frame_id) & (df['process'] == process) & (df['event'] == 'start')]['timestamp']
        end_time = df[(df['frame_id'] == frame_id) & (df['process'] == process) & (df['event'] == 'end')]['timestamp']

        if not start_time.empty and not end_time.empty:
            duration = end_time.values[0] - start_time.values[0]
            process_durations['frame_id'].append(frame_id)
            process_durations['process'].append(process)
            process_durations['duration'].append(duration)

# 转换为DataFrame
df_durations = pd.DataFrame(process_durations)

# 计算 ProcessA 和 ProcessB 的统计数据
process_a_durations = df_durations[df_durations['process'] == 'ProcessA']['duration']
process_b_durations = df_durations[df_durations['process'] == 'ProcessB']['duration']

# 计算平均耗时、P99 耗时和 P90 耗时
stats = {
    'ProcessA': {
        'average': process_a_durations.mean(),
        'P99': process_a_durations.quantile(0.99),
        'P90': process_a_durations.quantile(0.90)
},
    'ProcessB': {
        'average': process_b_durations.mean(),
        'P99': process_b_durations.quantile(0.99),
        'P90': process_b_durations.quantile(0.90)
}
}

# 计算系统的运行时间和总帧数
start_time = df['timestamp'].min()
end_time = df['timestamp'].max()
total_time_seconds = (end_time - start_time) / 1000.0  # 转换为秒

total_frames = df['frame_id'].nunique()

# 计算平均吞吐量
throughput = total_frames / total_time_seconds

# 计算每帧的平均处理时间（从 ProcessA 开始到 ProcessB 结束）
frame_processing_times = []

for frame_id in df['frame_id'].unique():
    process_a_start = df[(df['frame_id'] == frame_id) & (df['process'] == 'ProcessA') & (df['event'] == 'start')][
        'timestamp']
    process_b_end = df[(df['frame_id'] == frame_id) & (df['process'] == 'ProcessB') & (df['event'] == 'end')]['timestamp']

    if not process_a_start.empty and not process_b_end.empty:
        processing_time = process_b_end.values[0] - process_a_start.values[0]
        frame_processing_times.append(processing_time)

average_frame_processing_time = np.mean(frame_processing_times)

# 写入结果数据
result = {
    'stats': stats,
    'throughput': throughput,
    'average_frame_processing_time': average_frame_processing_time
}
output_file = r'C:\Users\Vicotiena\Desktop\python_project\log\result.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=4)
