from esp32api.communication import communication


# 示例 3：
# 保留旧接口写法，兼容现有工程。
# 如果客户暂时不想改原来的调用方式，可以继续这样使用。
communication.init_uart(port=2, baudrate=115200, tx=17, rx=16)

print(communication.getInfo())
print(communication.getReading())
