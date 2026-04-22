# 客户模式 V2 说明

## 入口

当前项目的默认启动入口是 [`main.py`](D:/Program Files/git/repository/Semeatech-Technology-Sensors/main.py)，内容为：

```python
from customer_mode_v2 import run
run()
```

这表示设备上电后会直接进入 [`customer_mode_v2.py`](D:/Program Files/git/repository/Semeatech-Technology-Sensors/customer_mode_v2.py)。

## 版本定位

V2 是当前默认的客户模式版本。

相比旧版客户模式，V2 的定位是：

- 保留原有 `esp32api` 协议层不变
- 把启动体验切换为更面向客户的流程
- 默认保存独立配置文件 `customer_mode_v2_config.json`

## 需要部署的文件

上传到设备时，建议至少包含：

- [`main.py`](D:/Program Files/git/repository/Semeatech-Technology-Sensors/main.py)
- [`customer_mode_v2.py`](D:/Program Files/git/repository/Semeatech-Technology-Sensors/customer_mode_v2.py)
- [`esp32api`](D:/Program Files/git/repository/Semeatech-Technology-Sensors/esp32api)

## 配置文件

V2 使用的配置文件为：

- `customer_mode_v2_config.json`

## 兼容性

旧的 V1 文件仍然保留在仓库中，便于回退和对比，但默认启动路径已经切换到 V2。
