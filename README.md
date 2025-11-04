# 项目使用说明（MicroPython UART 传感器集成）

## 📌 项目简介

本项目用于在 **MicroPython 支持的开发板** 上读取 UART 接口传感器的数据，并实现：

- 数据读取与解析（支持多种气体检测传感器）
- 校零与标定指令发送


适用于 **环境监测、气体检测、工业监控等嵌入式 IoT 场景**。

---

## 🚀 快速开始（适用于零基础用户）

### ✅ 你需要准备

| 项目 | 推荐/说明 |
|------|-----------|
| 开发板 | ESP32 / ESP8266（支持 MicroPython） |
| 传感器 | UART 通信的气体传感器模块Sensors |
| 工具 | USB 数据线、电脑 |
| 软件 | MicroPython 固件、[Thonny 编辑器](https://thonny.org/)（或 uPyCraft） |

---

### 🛠️ 1. 安装 MicroPython 到开发板

### ✅ 一、准备工具和文件

| 工具/文件          | 说明                                                                |
| -------------- | ----------------------------------------------------------------- |
| MicroPython 固件 | 从官方 [MicroPython 官网](https://micropython.org/download/) 下载对应板子的固件 |
| Thonny IDE     | 推荐的图形化 IDE，支持一键烧录 MicroPython                                     |
| USB 数据线        | 用于连接开发板到电脑                                                        |
| 驱动程序           | 如果电脑无法识别开发板，请安装驱动（如 CP210x、CH340）                                 |

---

### ✅ 二、下载并安装 Thonny 编辑器（推荐）

1. 访问官网下载安装：
   👉 [https://thonny.org](https://thonny.org)

2. 安装完成后，打开 Thonny。

---

### ✅ 三、连接开发板并安装固件

#### 👉 1. 连接开发板

* 用 USB 数据线将 ESP32 / ESP8266 开发板连接到电脑
* 打开 Thonny，在状态栏底部看到类似 `MicroPython (no device selected)` 或者 `Python (PC)`。

#### 👉 2. 安装 MicroPython 固件

在 Thonny 中依次执行：

* 菜单栏点击：**工具** → **安装或更新 MicroPython 固件**

* 在弹出的窗口中选择：

  | 选项            | 说明                                                         |
  | ------------- | ---------------------------------------------------------- |
  | **端口 (Port)** | 通常是 `COMx`（Windows）或 `/dev/ttyUSBx`（Linux/Mac），若不显示可点击「刷新」 |
  | **板子类型**      | 选择 `ESP32` 或 `ESP8266`，根据你的开发板型号选择                         |
  | **固件版本**      | 点击右侧「在线下载固件」，选择稳定版固件即可（也可以手动从官网下载 `.bin` 文件）               |

* 点击【安装】开始烧录固件。整个过程大约 10\~30 秒。

> 🔧 若遇到无法进入烧录状态的情况，可尝试按住开发板上的 `BOOT` 键，再点击「安装」。

---

### ✅ 四、验证固件是否安装成功

烧录完成后：

* 底部状态栏应显示为：`MicroPython (ESP32) - COMx` 或类似字样。
* 点击 Thonny 的 Shell（终端）窗口，输入：

```python
print("Hello MicroPython!")
```

输出正常说明烧录成功 🎉

---

## 🔄 可选：使用 esptool 手动烧录（高级用户）

如果你不使用 Thonny，也可以用 `esptool.py` 手动烧录：

```bash
pip install esptool
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 --port COMx --baud 460800 write_flash -z 0x1000 esp32-xxxxxx.bin
```

> 替换 `COMx` 为你电脑识别的串口号，`esp32-xxxxxx.bin` 为你的固件文件名。

---

### ✅ 安装成功后你可以继续：

* 将本项目文件上传到开发板（`main.py`、各工具类）
* 连接 UART 传感器，开始读取数据

---



### ✍️ 2. 运行项目代码

#### ✅ 下载项目代码

你可以通过 Git 克隆项目或直接下载 `.zip` 文件解压。

```bash
git clone https://github.com/semeateh/Semeatech-Technology-Sensors.git
```

#### ✅ 连接开发板

- 打开 Thonny
- 选择 MicroPython 设备（通常是 COMx 或 /dev/ttyUSBx）
- 将以下文件上传到开发板：

```
main.py
communication.py
test.py
```

> **提示**：在 Thonny 左侧「文件」区右键 -> 上传文件。

#### ✅ 开始运行

将 UART 传感器的 TX、RX 正确连接到板子（例如 GPIO16 和 GPIO17），然后运行 `test.py`,输入相应指令。

    ================ UART 初始化 =================
     请选择 UART 串口号 (1 或 2) [默认 2]: 1
     请输入波特率 (推荐: 4系=9600, 7系=115200) [默认 115200]: 9600
     请输入 TX 引脚编号（ESP32默认17） [默认 17]: 17
     请输入 RX 引脚编号（ESP32默认16） [默认 16]: 16
     ✅ UART 初始化完成: UART(1), 波特率=9600, TX=17, RX=16
     
    [1] 读取模块信息 (getInfo)
    [2] 读取实时数据 (getReading)
    [3] 读取标气浓度 (getSpanValue)
    [4] 零点标定（聚合：7优先→4）
    [5] 跨度标定（聚合：7优先→4）  ← 会询问 PPM
    [T] 读取温度 (getTemp)   | 仅 7 系列
    [H] 读取湿度 (getHumi)   | 仅 7 系列
    [Q] 退出
    
   
你将在 Thonny 的「Shell」窗口看到解析后的数据输出：
```
示例：输入 `1`
--- getInfo() ---
OK?: True
raw: AA 0F 01 0B 01 F4 00 64 00 32 00 19 02 8A E5 EE
info: NH3 (code=11)
```
示例：输入 `2`
--- getReading() ---
OK?: True
raw: AA 01 01 00 00 08 00 3B CA EE
parsed: 2048 ppm
```
示例：输入 `3`
--- getSpanValue() ---
OK?: True
raw: AA 01 01 00 00 08 00 3B CA EE
value: 2048 ppm
```

---

### 🔌 3. 如何连接传感器（示例接线）

| 传感器引脚 | ESP32 GPIO |                                                  
|------------|-------------|                                                           
| VCC        | 3.3V        |
| GND        | GND         |
| TX         | GPIO16 (RX2) |
| RX         | GPIO17 (TX2) |

请根据你的开发板引脚图和传感器说明书调整。

例以 ESP32和7 SMART Sensor Module传感器模块图。

![screenshot-1746511969470](https://github.com/user-attachments/assets/3d6a5311-76e0-4742-bd4b-44c3a3e9c56b)            ![screenshot-1746511716478](https://github.com/user-attachments/assets/89b9d5f5-4bd8-4792-947c-ff1d2b53a3b2)


---

### 📦 4. 如何将本项目集成到你的项目中？

如果你有自己的项目结构，可以这样整合：

#### ✅ 1. 复制以下模块文件：

- `communication.py`



#### ✅ 2. 在你的主程序中调用：

```python
from communication import communication

# ✅ 第一步：选择使用的 UART 串口
# 若使用 ESP32，可选 UART(1) / UART(2)
# 若使用树莓派 Pico，可选 UART(0) / UART(1)
# 你可以根据硬件连接修改：
class _UARTWrapper:
    def __init__(self, port=2, baudrate=9600, tx=None, rx=None, timeout=300):
        if _MICROPY:
            self.uart = UART(port, baudrate=baudrate, tx=tx or 17, rx=rx or 16, timeout=timeout)
        else:
            self.uart = _MockUART()


# ✅ 第二步（可选）：修改模块地址或 ID
# 默认：
#   4 系列模块地址：0x01
#   7 系列模块 ID ：0x10
# 若需要更改，可直接调用：
communication.set_address(addr_4=0x02, id_7=0x12)
# 该命令在运行时立即生效，无需改动源码

# ✅ 第三步：读取模块信息（自动识别系列）
print(communication.getInfo())

# ✅ 第四步：读取实时数据
print(communication.getReading())

# ✅ 第五步：零点标定
print(communication.zeroCal())

# ✅ 第六步：跨度标定（任意 PPM，自动计算 CRC）
print(communication.spanCal(250))

# ✅ 第七步：获取温湿度（仅 7 系列支持）
print("温度:", communication.getTemp())
print("湿度:", communication.getHumi())
```
---

## 📘 项目结构说明

### 1. `Main` 类
核心逻辑所在，包括：
- UART 初始化
- 循环读取传感器数据
- 数据解析与打印
- 心跳机制

### 2. `communication` 类
- 解析传感器返回的 hex 数据
- 映射气体类型
- 返回浓度值、单位、状态等信息



---

## 📖 常见问题解答

### 1. **如何知道我的传感器型号？**
请查阅传感器手册，确认是否为 UART 通信，并获取通信协议文档。

### 2. **为什么接了传感器没反应？**
- 检查接线是否正确（TX <-> RX）
- 检查波特率是否匹配（默认 9600 或 115200）
- 使用 `uart.any()` 检查是否有数据返回

### 3. **UART 数据不完整怎么办？**
建议在 `uart.read()` 前加入 `utime.sleep(0.1)` 短暂等待，确保数据完整接收。

### 4. **如何将数据发送到服务器？**
你可以在读取数据后使用 MQTT、HTTP 等方式上传。

---

## 🧩 后续扩展建议

- 增加 Web 配置页面（如配置 WiFi 和 MQTT）
- 支持多传感器并发读取
- 将数据储存到本地（如 SD 卡）

---

## 📄 许可证

本项目使用 MIT 许可证，详情请见 [LICENSE](./LICENSE)。

---

