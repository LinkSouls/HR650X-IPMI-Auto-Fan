'''
Author: Yuzhuo Wu
Date: 2023-12-07 19:19:28
LastEditTime: 2023-12-07 20:02:43
LastEditors: Yuzhuo Wu
Description: IPMI风扇自动控制脚本
FilePath: \HR650X-IPMI-Auto-Fan\ipmi_manager.py
今天也是认真工作的一天呢
'''
import subprocess
import re
import time
import datetime

# 风扇速度配置
# 格式: [温度范围最小值, 温度范围最大值]: 风扇速度百分比
FAN_SPEEDS = [
    {'temp_range': [0, 5], 'speed': 2},    # 系统关闭时
    {'temp_range': [5, 40], 'speed': 10},  # 低温
    {'temp_range': [40, 45], 'speed': 14},
    {'temp_range': [45, 50], 'speed': 20},
    {'temp_range': [50, 60], 'speed': 50},
    {'temp_range': [60, 80], 'speed': 80},
    {'temp_range': [80, 100], 'speed': 100}
]

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_message(message):
    """记录日志到文件"""
    timestamp = get_timestamp()
    with open('ipmi_fan.log', 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} {message}\n")
    print(f"{timestamp} {message}")

def get_temperature():
    # 本地执行IPMI命令获取温度
    cmd = "ipmitool sensor | grep CPU | grep Temp"
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    if process.returncode != 0:
        log_message(f"Error executing command: {cmd}. Error: {error}")
        return None

    output = output.decode('utf-8')
    lines = output.split('\n')
    temperatures = []

    for line in lines:
        if not line.strip():  # 跳过空行
            continue
            
        try:
            parts = line.split('|')
            if len(parts) < 2:  # 确保有足够的部分
                continue
                
            value = parts[1].strip()
            if value == 'na':
                temperatures.append(float(0))  
                log_message('The system is off, tempature is na')
                continue
                
            if 'Temp' in line:
                temp = re.findall(r'\d+\.\d+', line)
                if temp:
                    temperatures.append(float(temp[0]))
        except (IndexError, ValueError) as err:
            log_message(f"Error processing line: {line}")
            log_message(f"Error details: {err}")
            continue

    if not temperatures:
        log_message("No temperature data found.")
        return None
    
    return max(temperatures)

def set_fan_speed(speed):
    # 本地执行IPMI命令设置风扇速度
    cmd = f"ipmitool raw 0x2e 0x30 00 00 {speed}"
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    if process.returncode != 0:
        log_message(f"Error executing command: {cmd}. Error: {error}")
        return False

    return True

def get_fan_speed(temp, fan_speeds):
    for fan_speed in fan_speeds:
        if fan_speed['temp_range'][0] <= temp < fan_speed['temp_range'][1]:
            return fan_speed['speed']
    return 100

def main():
    temp = get_temperature()
    if temp is None:
        return

    speed = get_fan_speed(temp, FAN_SPEEDS)
    if set_fan_speed(speed):
        log_message(f"Set fan speed to {speed}% for CPU temperature {temp}°C")

if __name__ == "__main__":
    log_message("IPMI风扇控制程序启动")
    try:
        while True:
            main()
            time.sleep(5)
    except KeyboardInterrupt:
        log_message("程序已安全退出")
