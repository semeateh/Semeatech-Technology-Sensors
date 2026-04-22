# esp32api 包对外导出入口
#
# 保留原有导出：
# - communication
# - Main
#
# 新增导出：
# - SensorClient

from esp32api.client import SensorClient
from esp32api.communication import communication

try:
    from esp32api.Main import Main
except Exception:
    # 在桌面 Python 验证环境里，Main 可能依赖 MicroPython 专属模块。
    # 这里允许降级为 None，避免影响 SDK 的导入和开发调试。
    Main = None
