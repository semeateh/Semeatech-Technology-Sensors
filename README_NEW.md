# Semeatech Technology Sensors

基于 MicroPython 的 UART 传感器接入项目，用于在 ESP32 / ESP8266 上读取 Sematech 4 系列、7 系列气体传感器数据，并支持校零、标定、温湿度读取等功能。

## 项目能做什么

- 通过 UART 与传感器通信
- 自动识别 4 系列 / 7 系列传感器
- 读取模块信息、实时浓度、标气浓度
- 执行零点标定、跨度标定
- 读取 7 系列温度、湿度数据
- 作为工程调试工具使用
- 作为客户可直接操作的设备程序使用
- 作为客户二次开发时可导入的 SDK 使用

适用场景：

- 环境监测
- 气体检测
- 工业监控
- 嵌入式 IoT 设备接入

## 当前版本：V3

本仓库当前已经形成三种使用方式：

### 1. 工程模式

适合研发、调试、协议联调。

- 入口文件：[`esp32api/test.py`]
- 特点：菜单式测试入口，手动输入 UART 参数
- 当前状态：菜单交互保持原样，但底层已经切换为 `SensorClient`
- 面向对象：工程师、调试人员

### 2. 客户模式 V2

适合交付后的最终客户直接使用。

- 入口文件：[`main.py`]
- 实际执行：[`customer_mode_v2.py`]
- 特点：状态首页、自动检测串口参数、自动保存配置、向导式校零/标定、连接设置
- 当前状态：客户交互流程保持原样，但底层已经切换为 `SensorClient`
- 面向对象：非技术客户、现场操作人员

### 3. SDK 集成模式 V3

适合客户把本项目直接集成进自己的 MicroPython 工程。

- 入口类：[`esp32api/client.py`] 中的 `SensorClient`
- 特点：支持客户自己创建 `UART(...)` 并注入，也支持直接传串口参数
- 面向对象：客户二次开发人员、嵌入式开发者

## V3 相比之前新增了什么

在保留原有 `communication` 静态接口的基础上，V3 增加了以下能力：

1. 新增 `SensorClient` 实例化接口
2. 支持客户直接传入已经初始化好的 UART 对象
3. 保留旧接口兼容，不影响原有工程
4. `esp32api/test.py` 底层已经切换为 `SensorClient`
5. `customer_mode_v2.py` 底层已经切换为 `SensorClient`
6. 新增 SDK 开发文档和示例代码

一句话概括：

- 老项目可以继续按原来的方式用
- 新项目可以按 SDK 的方式接入

## 仓库结构

```text
.
├─ main.py                     # 客户模式自动启动入口
├─ customer_mode_v2.py         # 客户模式 V2
├─ CUSTOMER_MODE_V2.md         # 客户模式说明
├─ SDK_GUIDE.md                # SDK 集成文档
├─ examples/                   # SDK 示例
│  ├─ sdk_with_uart_object.py
│  ├─ sdk_with_params.py
│  └─ legacy_compat.py
├─ esp32api/
│  ├─ communication.py         # 核心协议层，保留旧接口
│  ├─ client.py                # V3 新增的 SensorClient
│  ├─ test.py                  # 工程模式测试入口
│  ├─ Main.py                  # 旧版主流程 / 扩展示例
│  └─ __init__.py              # 包导出入口
├─ boot.py
└─ lib/
   └─ ntptime.mpy
```

## 核心文件说明

### `esp32api/communication.py`

这是项目的核心协议层，负责：

- UART 收发
- 4 系列 / 7 系列指令封装
- 原始十六进制数据解析
- 气体类型映射
- CRC 计算
- 保留原有 `communication.xxx()` 静态调用方式

主要接口：

- `communication.init_uart(...)`
- `communication.getInfo()`
- `communication.getReading()`
- `communication.getSpanValue()`
- `communication.zeroCal()`
- `communication.spanCal(ppm)`
- `communication.getTemp()`
- `communication.getHumi()`

### `esp32api/client.py`

这是 V3 新增的 SDK 客户端层，主要用于客户二次开发。

主要接口：

- `SensorClient(uart=...)`
- `SensorClient(port=..., baudrate=..., tx=..., rx=...)`
- `getInfo()`
- `getReading()`
- `getSpanValue()`
- `zeroCal()`
- `spanCal(ppm)`
- `getTemp()`
- `getHumi()`
- `set_uart(...)`
- `set_address(...)`
- `get_config()`

### `esp32api/test.py`

工程模式测试脚本，适合内部调试。

特点：

- 菜单式交互
- 手动输入串口参数
- 手动执行读取/校准动作
- 当前底层已切换到 `SensorClient`

### `main.py`

MicroPython 设备上电后的自动入口。当前作用是把启动流程切换到客户模式 V2。

### `customer_mode_v2.py`

客户模式交互层，主要能力包括：

- 自动检测 UART 参数
- 自动保存 / 加载配置
- 状态首页
- 中文提示
- 校零向导
- 标定向导
- 连接设置
- 当前底层已切换到 `SensorClient`

## 功能列表

| 功能 | 说明 |
|------|------|
| `getInfo()` | 读取模块信息并识别气体类型 |
| `getReading()` | 读取实时浓度数据 |
| `getSpanValue()` | 读取标气浓度 |
| `zeroCal()` | 零点标定 |
| `spanCal(ppm)` | 跨度标定 |
| `getTemp()` | 读取温度，仅 7 系列 |
| `getHumi()` | 读取湿度，仅 7 系列 |

## 你需要准备

| 项目 | 推荐 / 说明 |
|------|-----------|
| 开发板 | ESP32 / ESP8266，支持 MicroPython |
| 传感器 | UART 通信的 Sematech 气体传感器 |
| 工具 | USB 数据线、电脑 |
| 软件 | MicroPython 固件、[Thonny](https://thonny.org/) |

## 快速开始

### 第 1 步：烧录 MicroPython

推荐使用 Thonny：

1. 打开 Thonny
2. 进入“工具”或“运行 -> 选择解释器”中的固件安装入口
3. 选择开发板型号与串口
4. 烧录对应固件

验证方法：

```python
print("Hello MicroPython!")
```

如果能正常输出，说明固件可用。

### 第 2 步：下载项目

```bash
git clone https://github.com/semeateh/Semeatech-Technology-Sensors.git
```

### 第 3 步：连接传感器

典型接线如下：

| 传感器引脚 | ESP32 GPIO |
|------------|------------|
| VCC | 3.3V |
| GND | GND |
| TX | GPIO16（接开发板 RX） |
| RX | GPIO17（接开发板 TX） |

注意：

- `TX` 和 `RX` 要交叉连接
- 开发板与传感器必须共地
- 如果传感器不是 3.3V 电平，请按硬件说明处理

### 第 4 步：上传文件到开发板

#### 如果你要使用客户模式

建议上传：

```text
main.py
customer_mode_v2.py
esp32api/
```

#### 如果你要使用工程模式

至少上传：

```text
esp32api/communication.py
esp32api/client.py
esp32api/test.py
esp32api/__init__.py
```

#### 如果你要给客户做 SDK 集成

建议至少上传：

```text
esp32api/communication.py
esp32api/client.py
esp32api/__init__.py
```

### 第 5 步：选择运行方式

#### 方式 A：客户模式 V2

运行根目录 `main.py`，或设备上电后自动执行。

首次运行时会：

- 自动尝试常见 UART 参数组合
- 自动识别是否连上传感器
- 自动保存成功配置
- 自动显示状态首页

配置文件：

```text
customer_mode_v2_config.json
```

#### 方式 B：工程模式

运行 [`esp32api/test.py`]，进入测试菜单。

可执行：

- 读取模块信息
- 读取实时数据
- 读取标气浓度
- 零点标定
- 跨度标定
- 读取温度 / 湿度

#### 方式 C：SDK 集成模式 V3

客户可以把这个项目像工具包一样接入。

方式 1：传入自己创建好的 UART

```python
from machine import UART, Pin
from esp32api import SensorClient

uart = UART(2, baudrate=115200, tx=Pin(17), rx=Pin(16))
client = SensorClient(uart=uart)

print(client.getInfo())
print(client.getReading())
```

方式 2：直接传串口参数

```python
from esp32api import SensorClient

client = SensorClient(port=2, baudrate=115200, tx=17, rx=16)

print(client.getInfo())
print(client.getReading())
```

如果只传 `port`，SDK 会按默认硬件约定自动补齐波特率：

- `port=1` 默认 `9600`
- `port=2` 默认 `115200`

## 旧接口兼容

为了兼容旧项目，原来的写法仍然保留：

```python
from esp32api.communication import communication

communication.init_uart(port=2, baudrate=115200, tx=17, rx=16)
communication.addr_4 = 0x01
communication.id_7 = 0x10

print(communication.getInfo())
print(communication.getReading())
print(communication.getSpanValue())
print(communication.zeroCal())
print(communication.spanCal(250))
print(communication.getTemp())
print(communication.getHumi())
```

## 常见输出示例

### 4 系列示例

```text
--- getInfo() ---
OK?: True
raw: AA 0F 01 0B 01 F4 00 64 00 32 00 19 02 8A E5 EE
info: NH3 (code=11)
```

```text
--- getReading() ---
OK?: True
raw: AA 01 01 00 00 08 00 3B CA EE
parsed: 2048 ppm
```

### 7 系列示例

```text
--- getInfo() ---
OK?: True
raw: 3A 10 01 02 8D 68
info: CO (code=2)
```

```text
--- getReading() ---
OK?: True
raw: 3A 10 03 00 00 06 00 00 00 08 00 00 00 07 09 3F 15 9E 77 6B
parsed: 浓度值: 8 μg/m³, 浓度值: 7ppb, 温度值: 23.67°C, 湿度值: 55.34%RH
```

## 常见问题

### 1. 接上传感器没反应怎么办

建议按顺序检查：

1. 传感器是否上电
2. `TX` / `RX` 是否接反
3. 波特率是否匹配
4. 当前是否选对 UART 口
5. 传感器是否确实使用 UART 协议

### 2. 如何知道我的模块属于 4 系列还是 7 系列

可以直接调用：

```python
print(communication.getInfo())
```

或者：

```python
print(client.getInfo())
```

项目会优先尝试识别 7 系列，再尝试 4 系列。

### 3. 客户自己的工程里可以用 UART1、UART2 或其他串口吗

可以。只要目标开发板和固件支持，客户就可以在自己的工程里这样写：

```python
uart = UART(1, baudrate=9600, tx=..., rx=...)
```

或者：

```python
uart = UART(2, baudrate=115200, tx=..., rx=...)
```

然后把这个 UART 传给 `SensorClient`。

按当前项目默认硬件约定：

- `UART(1)` 对应 `4系列`，默认波特率 `9600`
- `UART(2)` 对应 `7系列`，默认波特率 `115200`

如果客户使用的是不同的主控板或不同的串口分配，也可以自己指定新的 `UART(...)` 参数。

### 4. UART 数据不完整怎么办

建议在发送后适当等待，例如 `100ms` 左右，确保返回帧接收完整。

### 5. 如何把数据上传到服务器

当前仓库核心关注的是“传感器接入与解析”。拿到结果后，你可以继续集成：

- MQTT
- HTTP
- WebSocket
- 本地文件存储

## 后续扩展建议

- 增加 Web 配置页面
- 加入 Wi-Fi 配网
- 支持 MQTT 自动上报
- 支持多传感器并发读取
- 支持日志导出
- 继续优化客户模式文案与现场排障提示

## 许可说明

本项目使用 MIT License，详见 [LICENSE](./LICENSE)。
