import os
import json
import socket
import subprocess
import http.client
import re

API_HOST = "127.0.0.1" # Please set of your IP
API_PORT = 8000 # Please set of your Port 
API_PATH = "/monitor" # Please set of API Points
IP_ADD = "XX.XX.XX.XX" # Please set of your IP
def get_hostname():
    """ホスト名を取得"""
    return socket.gethostname()

def get_cpu_usage():
    """CPU使用率を取得（top コマンドを使用し、100 - idle を計算）"""
    try:
        result = subprocess.run(["top", "-bn1"], capture_output=True, text=True)
        match = re.search(r"(\d+\.\d+)\s*id", result.stdout)
        if match:
            idle = float(match.group(1))
            return round(100.0 - idle, 2)  # 100 - idle でCPU使用率を計算
    except Exception as e:
        print(f"Error fetching CPU usage: {e}")
    return 0.0  # 取得失敗時は 0.0 を返す

def get_memory_info():
    """メモリ使用量と総メモリ量を取得（free コマンドを使用）"""
    try:
        result = subprocess.run(["free", "-b"], capture_output=True, text=True)
        lines = result.stdout.split("\n")
        mem_info = lines[1].split()
        total_memory = int(mem_info[1])
        used_memory = total_memory - int(mem_info[3])  # `free` の値を引く
        return used_memory, total_memory
    except Exception as e:
        print(f"Error fetching memory info: {e}")
    return 0, 0  # 取得失敗時は 0 を返す

def get_gpu_metrics():
    """nvidia-smi を用いて GPU 名前、使用率、メモリ情報を取得"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True
        )
        gpu_data = result.stdout.strip().split("\n")
        if not gpu_data:
            return None

        name, usage, mem_used, mem_total = gpu_data[0].split(", ")
        return {
            "gpu_name": name.strip(),
            "gpu_usage": int(usage),
            "gpu_memory_usage": int(mem_used),
            "gpu_total_memory": int(mem_total)
        }
    except Exception as e:
        print(f"Error fetching GPU metrics: {e}")
        return None

def get_top_gpu_user():
    """最もVRAMを使用しているユーザーを取得（標準ライブラリのみ使用）"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True
        )
        processes = result.stdout.strip().split("\n")

        if not processes or processes[0] == "":
            return ""  # 実行中のプロセスがない場合、空文字を返す

        max_memory = 0
        top_user = ""

        for process in processes:
            pid, used_mem = process.split(", ")
            pid = int(pid)
            used_mem = int(used_mem)

            if used_mem > max_memory:
                max_memory = used_mem
                try:
                    top_user = subprocess.run(
                        ["ps", "-o", "user=", "-p", str(pid)],
                        capture_output=True,
                        text=True
                    ).stdout.strip()
                except Exception as e:
                    print(f"Error fetching user for PID {pid}: {e}")

        return top_user if top_user else ""
    except Exception as e:
        print(f"Error fetching GPU process data: {e}")
        return ""

def send_data():
    """取得したデータをAPIサーバーに送信（http.client を使用）"""
    hostname = get_hostname()
    cpu_usage = get_cpu_usage()
    memory_usage, total_memory = get_memory_info()
    user = get_top_gpu_user()
    gpu_data = get_gpu_metrics()

    system_data = {
        "hostname": hostname,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "total_memory": total_memory,
        "runner": user,
        "ip": IP_ADD
    }

    if gpu_data:
        system_data.update(gpu_data)
    json_data = json.dumps(system_data)

    try:
        conn = http.client.HTTPConnection(API_HOST, API_PORT)
        headers = {"Content-Type": "application/json"}
        conn.request("POST", API_PATH, body=json_data, headers=headers)
        response = conn.getresponse()
        print("Response:", response.status, response.read().decode())
        conn.close()
    except Exception as e:
        print(f"Error sending data: {e}")

if __name__ == "__main__":
    send_data()

