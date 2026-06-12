# Sematech Sensors SDK 集成指南

本文档面向需要把 Sematech 传感器接入自己 MicroPython 项目的开发者。项目总览、客户模式和工程模式说明见 [README.md](./README.md)。

## 1. 快速接入

推荐方式是由客户自己的工程创建 `UART(...)`，然后传给 `SensorClient`。

```python
from machine import UART, Pin
from esp32api import SensorClient

uart = UART(2, baudrate=115200, tx=Pin(17), rx=Pin(16))
client = SensorClient(uart=uart)

print(client.getInfo())
print(client.getReading())
```

也可以直接传串口参数，让 SDK 内部创建 UART。

```python
from esp32api import SensorClient

client = SensorClient(port=2, tx=17, rx=16)

print(client.getInfo())
print(client.getReading())
```

默认硬件约定：

| 串口 | 传感器系列 | 默认波特率 |
|------|------------|------------|
| `UART(1)` | 4 系列 | `9600` |
| `UART(2)` | 7 系列 | `115200` |

如果客户硬件不同，可以显式传入自己的 `baudrate`、`tx`、`rx` 或完整 `UART(...)` 对象。

## 2. 部署文件

SDK 集成至少需要上传：

```text
esp32api/communication.py
esp32api/client.py
esp32api/__init__.py
```

如果需要参考示例，可同时保留：

```text
examples/
```

## 3. 返回值约定

公开接口统一返回 `dict`，常见字段如下：

| 字段 | 说明 |
|------|------|
| `ok` | 是否成功 |
| `series` | 识别到的系列，常见为 `4` 或 `7` |
| `raw` | 原始十六进制响应 |
| `info` | 模块信息 |
| `parsed` | 解析后的读数或说明 |
| `value` | 数值类结果 |
| `result` | 操作结果，如校零或标定结果 |
| `request` | 标定类接口发出的请求帧 |
| `response` | 标定类接口收到的响应帧 |
| `note` | 失败或补充提示 |
| `note2` | 附加说明 |

建议客户代码先判断 `ok`：

```python
result = client.getReading()
if result.get("ok"):
    print("读取成功:", result)
else:
    print("读取失败:", result.get("note") or result)
```

## 4. 初始化接口

### `SensorClient(...)`

用途：创建传感器 SDK 客户端。

参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `uart` | 外部已创建好的 UART 对象 | `None` |
| `port` | UART 串口号 | `None` |
| `baudrate` | 波特率 | 根据 `port` 推导 |
| `tx` | TX 引脚，支持整数或 `Pin(...)` | `None` |
| `rx` | RX 引脚，支持整数或 `Pin(...)` | `None` |
| `timeout` | 串口超时，单位毫秒 | `300` |
| `addr_4` | 4 系列地址 | `0x01` |
| `id_7` | 7 系列设备 ID | `0x10` |

规则：

- 传入 `uart` 时，SDK 复用该对象
- 未传 `uart` 时，必须至少传入 `port`
- 只传 `port=1` 时，默认波特率为 `9600`
- 只传 `port=2` 时，默认波特率为 `115200`
- 显式传入 `baudrate` 时，SDK 保留用户值

成功示例：

```python
client = SensorClient(port=2, tx=17, rx=16)
print(client.get_config())
```

返回配置示例：

```python
{
    "port": 2,
    "baudrate": 115200,
    "tx": 17,
    "rx": 16,
    "timeout": 300,
    "addr_4": 1,
    "id_7": 16
}
```

失败注意事项：

- 未传 `uart` 且未传 `port` 会抛出 `ValueError`
- 串口号是否可用取决于开发板和 MicroPython 固件

### `set_uart(...)`

用途：运行时重新设置当前客户端使用的 UART。

参数与 `SensorClient(...)` 中的 UART 参数一致。

示例：

```python
client.set_uart(port=1, tx=17, rx=16)
print(client.get_config())
```

注意事项：

- 重新设置后，后续所有读取和标定都会使用新的 UART
- 传入外部 `uart` 对象时，SDK 不会重新创建底层串口

### `set_address(addr_4=None, id_7=None)`

用途：设置 4 系列地址或 7 系列设备 ID。

参数：

| 参数 | 说明 |
|------|------|
| `addr_4` | 4 系列地址，范围由设备协议决定 |
| `id_7` | 7 系列设备 ID，范围由设备协议决定 |

示例：

```python
client.set_address(addr_4=0x01, id_7=0x10)
```

返回值：返回当前 `client`，便于链式调用。

### `get_config()`

用途：查看当前 SDK 客户端配置。

示例：

```python
print(client.get_config())
```

返回字段：

```python
{
    "port": 2,
    "baudrate": 115200,
    "tx": 17,
    "rx": 16,
    "timeout": 300,
    "addr_4": 1,
    "id_7": 16
}
```

## 5. 读取接口

### `getInfo()`

用途：读取模块信息并识别气体类型。

参数：无。

成功示例：

```python
result = client.getInfo()
print(result)
```

返回示例：

```python
{
    "ok": True,
    "series": 7,
    "raw": "3A 10 01 02 8D 68",
    "info": "CO (code=2)"
}
```

失败示例：

```python
{
    "ok": False,
    "series": None,
    "raw": "",
    "info": ""
}
```

注意事项：

- 无返回通常表示接线、波特率、串口号或供电异常
- 当前实现会先尝试 7 系列协议，再尝试 4 系列协议

### `getReading()`

用途：读取实时浓度数据。

参数：无。

成功示例：

```python
result = client.getReading()
print(result)
```

4 系列返回示例：

```python
{
    "ok": True,
    "series": 4,
    "raw": "AA 01 01 00 00 08 00 3B CA EE",
    "parsed": "2048 ppm"
}
```

7 系列返回示例：

```python
{
    "ok": True,
    "series": 7,
    "raw": "3A 10 03 ...",
    "parsed": "浓度值: 8 μg/m³, 浓度值: 7ppb, 温度值: 23.67°C, 湿度值: 55.34%RH"
}
```

失败示例：

```python
{
    "ok": False,
    "series": None,
    "raw": "",
    "parsed": ""
}
```

### `getSpanValue()`

用途：读取标气浓度或量程信息。

参数：无。

成功示例：

```python
result = client.getSpanValue()
print(result)
```

4 系列返回示例：

```python
{
    "ok": True,
    "series": 4,
    "raw": "AA 01 01 00 00 08 00 3B CA EE",
    "value": "2048 ppm"
}
```

7 系列返回示例：

```python
{
    "ok": True,
    "series": 7,
    "raw": {
        "μg/m³": "3A 10 03 ...",
        "ppb": "3A 10 03 ..."
    },
    "value": {
        "μg/m³": "6μg/m³",
        "ppb": "6ppb"
    }
}
```

失败示例：

```python
{
    "ok": False,
    "series": None,
    "raw": "",
    "value": None
}
```

### `getTemp()`

用途：读取温度，仅 7 系列支持。

参数：无。

成功示例：

```python
print(client.getTemp())
```

返回示例：

```python
{
    "ok": True,
    "series": 7,
    "raw": "3A 10 03 00 04 01 09 49 45 C4",
    "value": "监测温度为:23.77°C"
}
```

不支持或无返回示例：

```python
{
    "ok": False,
    "series": None,
    "raw": "",
    "value": None
}
```

### `getHumi()`

用途：读取湿度，仅 7 系列支持。

参数：无。

成功示例：

```python
print(client.getHumi())
```

返回示例：

```python
{
    "ok": True,
    "series": 7,
    "raw": "3A 10 03 00 05 01 14 E3 CD 17",
    "value": "监测湿度为:53.47%RH"
}
```

不支持或无返回示例：

```python
{
    "ok": False,
    "series": None,
    "raw": "",
    "value": None
}
```

## 6. 校准接口

### `zeroCal()`

用途：执行零点标定。

参数：无。

示例：

```python
result = client.zeroCal()
print(result)
```

成功示例：

```python
{
    "ok": True,
    "series": 4,
    "raw": "AA 02 01 10 D0 5C EE",
    "result": "模块校零成功"
}
```

失败示例：

```python
{
    "ok": False,
    "series": None,
    "raw": "",
    "result": "无返回"
}
```

风险说明：

- 只能在洁净空气环境下执行
- 执行后会改变传感器校准状态
- 不建议在正常检测过程中自动执行

### `spanCal(ppm)`

用途：执行跨度标定，SDK 会根据输入浓度动态生成 CRC 帧。

参数：

| 参数 | 说明 |
|------|------|
| `ppm` | 标准气体浓度，范围会被限制到 `0~65535` |

示例：

```python
result = client.spanCal(250)
print(result)
```

返回示例：

```python
{
    "ok": True,
    "series": 7,
    "request": {
        "7": "3A 10 09 00 00 01 00 FA ...",
        "4": "AA 05 01 00 FA ... EE"
    },
    "response": {
        "7": "3A 10 09 00 ..."
    },
    "result": "标定结果:标定成功",
    "note2": "span=250 ppm, id7=0x10, addr4=0x01"
}
```

失败示例：

```python
{
    "ok": False,
    "series": None,
    "request": {
        "7": "...",
        "4": "..."
    },
    "response": {},
    "note": "无设备应答，请检查接线、电源和串口参数",
    "note2": "span=250 ppm, id7=0x10, addr4=0x01"
}
```

风险说明：

- 只能在接入标准气体且读数稳定后执行
- `ppm` 必须与标准气体标称浓度一致
- 执行后会改变传感器校准状态
- 不建议开放给未经培训的现场用户直接操作

## 7. 旧接口兼容

旧项目仍可继续使用 `communication`：

```python
from esp32api.communication import communication

communication.init_uart(port=2, tx=17, rx=16)

print(communication.getInfo())
print(communication.getReading())
```

默认规则与 `SensorClient` 一致：

- `communication.init_uart(port=1)` 使用 `9600`
- `communication.init_uart(port=2)` 使用 `115200`

新项目建议优先使用 `SensorClient`。

## 8. 常见问题

### 没有任何返回

检查顺序：

1. 传感器是否上电
2. `TX` 和 `RX` 是否交叉连接
3. 开发板和传感器是否共地
4. 波特率是否正确
5. 当前 UART 口是否正确
6. 传感器是否为 UART 协议

### 客户能不能用其他 UART

可以。客户可以自己创建任何目标板支持的 UART：

```python
uart = UART(1, baudrate=9600, tx=Pin(12), rx=Pin(13))
client = SensorClient(uart=uart)
```

只要该 UART 能正常 `write()` 和 `read()`，SDK 就可以复用。

### `UART(0)` 能不能用

取决于开发板。很多 ESP32 固件会把 `UART(0)` 用作 REPL 或下载调试口，不建议默认使用。

### 可以在一个项目里接多个传感器吗

可以创建多个 `SensorClient` 实例，每个实例绑定不同 UART。

```python
sensor_4 = SensorClient(port=1, tx=17, rx=16)
sensor_7 = SensorClient(port=2, tx=17, rx=16)
```

实际是否可行取决于开发板可用串口数量、引脚复用和供电能力。
