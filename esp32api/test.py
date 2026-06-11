# test.py
# 在 Thonny / MicroPython 环境下测试 4 系列 / 7 系列传感器通信与标定流程。
#
# 本次升级说明：
# - 保留原来的菜单交互方式，方便内部继续联调。
# - 底层由 communication 静态调用切换为 SensorClient 实例调用。
# - 这样既不改变测试使用习惯，也能覆盖新的 SDK 集成路径。

import json
import os

try:
    from esp32api import SensorClient
except Exception as e:
    print("无法导入 SensorClient，请确认文件已上传到设备根目录。")
    print("错误信息：", e)
    raise SystemExit

# ---------- 模块元信息 ----------
if "module.json" in os.listdir():
    try:
        with open("module.json") as f:
            meta = json.load(f)
            MODULE_NAME = meta.get("module", "Unknown")
            MODULE_VER = meta.get("version", "0.0")
    except Exception as e:
        MODULE_NAME, MODULE_VER = "Unknown", "0.0"
        print("读取 module.json 失败：", e)
else:
    # 如果文件不存在，则使用内置默认
    MODULE_NAME, MODULE_VER = "DemoModule", "1.0"

print(f"[模块信息] {MODULE_NAME} v{MODULE_VER}")
print("===============================================")

# ---------- 菜单 ----------
def build_menu():
    return """
================= Sematech 传感器通讯测试 =================
[1] 读取模块信息 (getInfo)
[2] 读取实时数据 (getReading)
[3] 读取标气浓度 (getSpanValue)
[4] 零点标定（聚合：7优先）
[5] 跨度标定（聚合：7优先） -> 会询问 PPM
[T] 读取温度 (getTemp)   | 仅 7 系列
[H] 读取湿度 (getHumi)   | 仅 7 系列
[Q] 退出
=========================================================
"""


def _print_result(title, result):
    print("\n--- %s ---" % title)
    if result is None:
        print("无返回")
        return

    try:
        ok = result.get("ok")
        print("OK?:", ok)
        for k, v in result.items():
            if k in ("req", "rsp", "raw"):
                print("%s: %s" % (k, v))
        if "info" in result:
            print("info:", result["info"])
        if "value" in result:
            print("value:", result["value"])
        if "parsed" in result:
            print("parsed:", result["parsed"])
        if "result" in result:
            print("result:", result["result"])
        if "note" in result:
            print("note:", result["note"])
        if "note2" in result:
            print("note2:", result["note2"])
    except Exception as e:
        print("打印结果时出错：", e)
        print("原结果对象：", result)


def ask_int(prompt, default=None, lo=0, hi=115200):
    try:
        label = f" [默认 {default}]" if default is not None else ""
        s = input("%s%s: " % (prompt, label)).strip()
        if s == "" and default is not None:
            return default
        v = int(float(s))
        if v < lo or v > hi:
            print(f"超出范围 [{lo}, {hi}]，已拒绝。")
            return None
        return v
    except Exception:
        print("请输入整数数值。")
        return None


def main():
    print("\n================ UART 初始化 ================")

    client = None
    try:
        port = ask_int("请选择 UART 串口号 (1=4系列, 2=7系列)", default=2, lo=1, hi=2)
        baud = ask_int("请输入波特率 (推荐: 4系=9600, 7系=115200)", default=115200)
        tx_pin = ask_int("请输入 TX 引脚编号（ESP32默认17）", default=17)
        rx_pin = ask_int("请输入 RX 引脚编号（ESP32默认16）", default=16)

        # 保留原有测试脚本的输入方式，但底层切换为 SensorClient。
        client = SensorClient(port=port, baudrate=baud, tx=tx_pin, rx=rx_pin)
    except Exception as e:
        print(f"UART 初始化失败：{e}")
        print("将使用默认 UART(2) TX=17 RX=16 配置。")
        client = SensorClient(port=2, baudrate=115200, tx=17, rx=16)

    while True:
        try:
            cmd = input(build_menu() + "请输入指令：").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if cmd == "1":
            _print_result("getInfo()", client.getInfo())

        elif cmd == "2":
            _print_result("getReading()", client.getReading())

        elif cmd == "3":
            _print_result("getSpanValue()", client.getSpanValue())

        elif cmd == "4":
            _print_result("zeroCal() 聚合", client.zeroCal())

        elif cmd == "5":
            span = ask_int("输入跨度标定浓度（PPM）", default=250)
            if span is not None:
                _print_result(f"spanCal({span}) 聚合", client.spanCal(span, prefer="7-first"))

        elif cmd == "T":
            _print_result("getTemp()", client.getTemp())

        elif cmd == "H":
            _print_result("getHumi()", client.getHumi())

        elif cmd == "Q":
            print("Bye.")
            break

        else:
            print("无效指令，请重试。")


if __name__ == "__main__":
    main()
