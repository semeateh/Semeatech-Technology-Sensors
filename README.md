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

1. 下载 MicroPython 固件（选择你的芯片类型）：  
   https://micropython.org/download/

2. 安装刷写工具（推荐使用 [Thonny](https://thonny.org/) 或 [esptool](https://github.com/espressif/esptool)）

3. 使用 Thonny：
   - 插上开发板，打开 Thonny
   - 工具栏选择「MicroPython (ESP32)」
   - 安装或升级固件：工具 > 安装 MicroPython 到设备 > 选择端口、上传固件

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
UAREIUtil.py
SensorDateUtil.py
SensorRespomseParser.py
FactoryUtil.py
test.py
```

> **提示**：在 Thonny 左侧「文件」区右键 -> 上传文件。

#### ✅ 开始运行

将 UART 传感器的 TX、RX 正确连接到板子（例如 GPIO16 和 GPIO17），然后运行 `test.py`,输入相应指令。

    # 4系列
    F_SENSOR_TYPE1 = "AA 0F 01 C5 80 EE"  # 终端读取模块信息命令
    F_SENSOR_NUM2 = "AA 01 01 C1 E0 EE"  # 终端发送浓度数据读取命令ppm
    F_SENSOR_MODULE_ZERO3 = "AA 02 01 C1 10 EE"  # 终端发送模块校零命令
    F_SENSOR_MODULE_ZERO3_TRUE = "AA 02 01 10 D0 5C EE"
    F_SENSOR_MODULE_CALIBRATION4 = "AA 03 01 C0 80 EE"  # 终端发送模块标定命令
    F_SENSOR_MODULE_CALIBRATION4_TRUE = "AA 03 01 10 81 9C EE"
    F_SENSOR_UPDATE_ADDRESS5 = "AA 04 02 82 B1 EE"  # 终端修改模块地址命令
    F_SENSOR_UPDATE_ADDRESS5_TRUE = "AA 04 02 10 30 AD EE"
    F_SENSOR_UPDATE_CONCENTRATION6 = "AA 05 01 01 F4 51 3F EE"  # 终端发送修改模块标气浓度命令
    F_SENSOR_UPDATE_CONCENTRATION6_TRUE = "AA 05 01 10 01 F4 E8 2E EE"

    # 7系列指令
    S_SENSOR_TYPE1 = "3A 10 01 00 00 01 00 00 82 B0"  # 类型
    S_SENSOR_NUM2 = "3A 10 03 00 00 02 00 00 73 52"  # 单位μg/m³
    S_SENSOR_NUM3 = "3A 10 03 00 02 02 00 00 72 EA"  # 单位ppb
    S_SENSOR_TEMPERATURE4 = "3A 10 03 00 04 01 00 00 82 62"  # 读取温度传感器数据 (单位为°C)
    S_SENSOR_HUMIDITY5 = "3A 10 03 00 05 01 00 00 83 9E"  # 读取湿度传感器数据 (单位为%RH)
    S_SENSOR_PARAMS6 = "3A 10 03 00 00 06 00 00 32 93"  # 读取多个参数 (地址0000 ~ 0005)
    S_SENSOR_CHECK7 = "3A 10 08 00 0A F9"  # 校验错误应答
    S_SENSOR_ZERO_CALIBRATION8 = "3A 10 07 00 00 01 00 00 82 D6"  # 零点标定
    S_SENSOR_SENSITIVITY_CALIBRATION9 = "3A 10 09 00 00 01 00 0A 03 FF"  # 灵敏度标定  D为00 0A 即：使用10PPM浓度气体进行标定

你将在 Thonny 的「Shell」窗口看到解析后的数据输出：

```
[UART] 收到数据: AA01020304...
Parsed Data: {'gas': 'CO', 'value': 4.12, 'unit': 'ppm'}
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

- `SensorDateUtil.py`
- `SensorRespomseParser.py`
- `FactoryUtil.py`


#### ✅ 2. 在你的主程序中调用：

```python
from esp32api.SensorResponseParser import SensorResponseParser
from esp32api.FactoryUtil import FactoryUtil
from esp32api.SensorDataUtil import SensorDataUtil  # 导入外部定义的SensorDataUtil类


# 初始化 UART 并读取数据
from machine import UART, Pin
uart = UART(1, baudrate=9600, tx=Pin(17), rx=Pin(16))

uart.write(FactoryUtil.by_type_get_return(1, 9600))
response = uart.read()
hex_str = ' '.join(f'{byte:02x}' for byte in response)
clean_str = SensorResponseParser.clean_string(hex_str)
data = SensorDataUtil.substring_data_4(clean_str, FlagCode.F_SENSOR_TYPE1)
print(data)
```

---

## 📘 项目结构说明

### 1. `Main` 类
核心逻辑所在，包括：
- UART 初始化
- 循环读取传感器数据
- 数据解析与打印
- 心跳机制

### 2. `SensorDateUtil` 类
- 解析传感器返回的 hex 数据
- 映射气体类型
- 返回浓度值、单位、状态等信息

### 3. `FlagCode` 类
预定义了传感器指令，如：
- `F_SENSOR_TYPE1`: 获取气体类型
- `F_SENSOR_NUM2`: 获取气体浓度
- `F_SENSOR_MODULE_ZERO3`: 发送校零指令
- `F_SENSOR_MODULE_CALIBRATION4`: 发送标定指令

### 4. `SensorRespomseParser` 类
数据处理工具类：
- Hex 字符串与 bytearray 转换
- 字符串清洗
- 十进制/十六进制转换

### 5. `FactoryUtil` 类
根据传感器类型生成指令，兼容不同波特率/型号。

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

