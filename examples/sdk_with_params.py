from esp32api import SensorClient


# 示例 2：
# 直接把串口参数交给 SDK，由 SDK 内部创建 UART。
# 这种方式更适合快速接入和简单脚本。
client = SensorClient(port=2, baudrate=115200, tx=17, rx=16)

print(client.get_config())
print(client.getInfo())
print(client.getReading())
