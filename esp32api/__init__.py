# esp32api 包对外导出入口
#
# V3 SDK 默认只导出 SensorClient。
#
# 旧接口继续通过原路径导入：
# from esp32api.communication import communication
# from esp32api.Main import Main
#
# 这样导入 SensorClient 时不会加载旧模块并提前创建 UART。

from esp32api.client import SensorClient
