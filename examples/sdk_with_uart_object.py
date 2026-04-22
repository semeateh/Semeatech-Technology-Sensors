from machine import UART, Pin

from esp32api import SensorClient


# 示例 1：
# 客户自己创建 UART，然后把 UART 对象传给我们的 SDK。
# 这种方式最适合客户已经有自己主程序和串口初始化逻辑的场景。
uart = UART(2, baudrate=9600, tx=Pin(17), rx=Pin(16))
client = SensorClient(uart=uart)

print(client.getInfo())
print(client.getReading())
