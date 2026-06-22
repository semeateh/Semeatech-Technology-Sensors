"""
V3 SensorClient 使用的私有兼容实现。

这里保留原有 SDK 所依赖的命令、解析和组帧行为，但不包含旧版
communication 静态接口，避免导入 SensorClient 时创建默认 UART。
"""

from time import sleep

try:
    from machine import UART, Pin

    _MICROPY = True
except ImportError:
    UART = None
    Pin = None
    _MICROPY = False


def clean_hex(s: str) -> str:
    return "".join(s.strip().upper().split())


def hex_to_bytes(hex_str: str) -> bytes:
    return bytes.fromhex(clean_hex(hex_str))


def bytes_to_hex(b: bytes) -> str:
    return " ".join(f"{x:02X}" for x in b)


def hex_to_decimal(hex_str: str) -> int:
    return int(clean_hex(hex_str), 16) if hex_str else 0


def clamp_u16(v: int) -> int:
    v = int(round(float(v)))
    return max(0, min(0xFFFF, v))


GAS_TYPE_MAPPING_4 = {
    0: "无",
    1: "EX",
    6: "C3H8",
    12: "CL2",
    16: "HBr",
    18: "AsH3",
    20: "Br2",
    25: "SiH4",
    26: "无",
    27: "无",
    28: "无",
    29: "无",
    30: "无",
    35: "无",
    36: "无",
    37: "C6H6",
    38: "H2O2",
    40: "VOC",
    2: "CO",
    3: "O2",
    4: "H2",
    5: "CH4",
    7: "CO2",
    8: "O3",
    9: "H2S",
    10: "SO2",
    11: "NH3",
    13: "ETO",
    14: "HCL",
    15: "PH3",
    17: "HCN",
    19: "HF",
    21: "NO",
    22: "NO2",
    23: "NOX",
    24: "CLO2",
    31: "THT",
    32: "C2H2",
    33: "C2H4",
    34: "CH2O",
    39: "C2H3CL",
    41: "CH3SH",
    42: "C4H8",
}

GAS_TYPE_MAPPING_7 = {
    0: "无",
    1: "无",
    6: "无",
    16: "无",
    18: "无",
    20: "无",
    25: "无",
    26: "无",
    27: "无",
    28: "无",
    29: "无",
    30: "无",
    35: "无",
    36: "无",
    37: "无",
    38: "无",
    2: "CO",
    3: "O2",
    4: "H2",
    5: "CH4",
    7: "CO2",
    8: "O3",
    9: "H2S",
    10: "SO2",
    11: "NH3",
    12: "CL2",
    13: "ETO",
    14: "HCL",
    15: "PH3",
    17: "HCN",
    19: "HF",
    21: "NO",
    22: "NO2",
    23: "NOX",
    24: "CLO2",
    31: "THT",
    32: "C2H2",
    33: "C2H4",
    34: "CH2O",
    39: "CH3SH",
    40: "C2H3CL",
}


def _map_gas(mapping: dict, code: int) -> str:
    return f"{mapping.get(code, '未知')} (code={code})"


def crc16_modbus(data: bytes) -> int:
    wcrc = 0xFFFF
    for b in data:
        wcrc ^= b
        for _ in range(8):
            if wcrc & 0x0001:
                wcrc = (wcrc >> 1) ^ 0xA001
            else:
                wcrc >>= 1
    return ((wcrc & 0xFF) << 8) | (wcrc >> 8)


class FlagCode:
    F_SENSOR_TYPE1 = "AA 0F 01 C5 80 EE"
    F_SENSOR_NUM2 = "AA 01 01 C1 E0 EE"
    F_SENSOR_MODULE_ZERO3 = "AA 02 01 C1 10 EE"
    F_SENSOR_MODULE_ZERO3_TRUE = "AA 02 01 10 D0 5C EE"
    F_SENSOR_MODULE_CALIBRATION4 = "AA 03 01 C0 80 EE"
    F_SENSOR_MODULE_CALIBRATION4_TRUE = "AA 03 01 10 81 9C EE"
    F_SENSOR_UPDATE_ADDRESS5 = "AA 04 02 82 B1 EE"
    F_SENSOR_UPDATE_ADDRESS5_TRUE = "AA 04 02 10 30 AD EE"
    F_SENSOR_UPDATE_CONCENTRATION6_TRUE = "AA 05 01 10 01 F4 E8 2E EE"

    S_HEADER = 0x3A
    S_DEFAULT_ID = 0x10
    S_SENSOR_TYPE1 = "3A 10 01 00 00 01 00 00 82 B0"
    S_SENSOR_NUM2 = "3A 10 03 00 00 02 00 00 73 52"
    S_SENSOR_NUM3 = "3A 10 03 00 02 02 00 00 72 EA"
    S_SENSOR_TEMPERATURE4 = "3A 10 03 00 04 01 00 00 82 62"
    S_SENSOR_HUMIDITY5 = "3A 10 03 00 05 01 00 00 83 9E"
    S_SENSOR_PARAMS6 = "3A 10 03 00 00 06 00 00 32 93"
    S_SENSOR_CHECK7 = "3A 10 08 00 0A F9"
    S_SENSOR_ZERO_CALIBRATION8 = "3A 10 07 00 00 01 00 00 82 D6"
    S_SENSOR_SENSITIVITY_CALIBRATION9 = "3A 10 09 00 00 01 00 0A 03 FF"


def substring_data_4(old_data: str, type_id: int) -> str:
    od = clean_hex(old_data)
    if type_id == 1:
        code = hex_to_decimal(od[6:8])
        return _map_gas(GAS_TYPE_MAPPING_4, code)
    if type_id == 2:
        return f"{hex_to_decimal(od[8:14])} ppm"
    if type_id == 3:
        return (
            "模块校零成功"
            if clean_hex(FlagCode.F_SENSOR_MODULE_ZERO3_TRUE) == od
            else "模块校零失败"
        )
    if type_id == 4:
        return (
            "模块标定成功"
            if clean_hex(FlagCode.F_SENSOR_MODULE_CALIBRATION4_TRUE) == od[:12]
            else "模块标定失败"
        )
    if type_id == 5:
        return (
            "地址修改成功"
            if clean_hex(FlagCode.F_SENSOR_UPDATE_ADDRESS5_TRUE) == od
            else "地址修改失败"
        )
    if type_id == 6:
        return (
            "修改模块标气浓度成功"
            if clean_hex(FlagCode.F_SENSOR_UPDATE_CONCENTRATION6_TRUE) == od
            else "修改模块标气浓度失败"
        )
    return ""


def substring_data_7(old_data: str, type_id: int) -> str:
    od = clean_hex(old_data)
    if type_id == 1:
        code = hex_to_decimal(od[6:8])
        return _map_gas(GAS_TYPE_MAPPING_7, code)
    if type_id == 2:
        return f"{hex_to_decimal(od[12:20])}μg/m³"
    if type_id == 3:
        return f"{hex_to_decimal(od[12:20])}ppb"
    if type_id == 4:
        return "监测温度为:" + f"{hex_to_decimal(od[12:16]) / 100:.2f}°C"
    if type_id == 5:
        return "监测湿度为:" + f"{hex_to_decimal(od[12:16]) / 100:.2f}%RH"
    if type_id == 6:
        d1 = hex_to_decimal(od[12:20])
        d2 = hex_to_decimal(od[20:28])
        d3 = hex_to_decimal(od[28:32]) / 100
        d4 = hex_to_decimal(od[32:36]) / 100
        return (
            f"浓度值: {d1} μg/m³, 浓度值: {d2}ppb, "
            f"温度值: {d3}°C, 湿度值: {d4}%RH"
        )
    if type_id == 8:
        return "零点标定返回数值:" + str(hex_to_decimal(od[12:16]))
    if type_id == 9:
        st = od[6:8]
        flag = (
            "标定成功"
            if st not in ("01", "02")
            else ("标定中" if st == "01" else "标定失败")
        )
        return "标定结果:" + flag
    return ""


class _MockUART:
    def __init__(self, *_, **__):
        self._buf = b""

    def write(self, data: bytes):
        print(f"[MOCK UART WRITE] {bytes_to_hex(data)}")

    def any(self) -> int:
        return len(self._buf)

    def read(self) -> bytes:
        out, self._buf = self._buf, b""
        return out

    def inject(self, hex_rsp: str):
        self._buf += hex_to_bytes(hex_rsp)


def _normalize_pin(pin):
    if pin is None or not _MICROPY:
        return pin
    if isinstance(pin, int):
        return Pin(pin)
    return pin


class _UARTWrapper:
    def __init__(
        self,
        port=2,
        baudrate=115200,
        tx=None,
        rx=None,
        timeout=300,
        uart=None,
    ):
        if uart is not None:
            self.uart = uart.uart if hasattr(uart, "uart") else uart
        elif _MICROPY:
            self.uart = UART(
                port,
                baudrate=baudrate,
                tx=_normalize_pin(17 if tx is None else tx),
                rx=_normalize_pin(16 if rx is None else rx),
                timeout=timeout,
            )
        else:
            self.uart = _MockUART()

    def send_hex_and_read(self, hex_cmd: str, delay_ms: int = 100) -> str:
        self.uart.write(hex_to_bytes(hex_cmd))
        sleep(max(delay_ms, 1) / 1000)
        resp = self.uart.read() or b""
        return bytes_to_hex(resp) if resp else ""


def build_4_update_span(addr: int, span_ppm: int) -> bytes:
    addr &= 0xFF
    span = clamp_u16(span_ppm)
    frame_wo_crc = bytes([0x05, addr, (span >> 8) & 0xFF, span & 0xFF])
    crc = crc16_modbus(frame_wo_crc)
    crc_h, crc_l = (crc >> 8) & 0xFF, crc & 0xFF
    return bytes([0xAA]) + frame_wo_crc + bytes([crc_h, crc_l, 0xEE])


def build_7_sensitivity_cal(dev_id: int, span_ppm: int) -> bytes:
    dev_id &= 0xFF
    span = clamp_u16(span_ppm)
    body = bytes(
        [
            0x3A,
            dev_id,
            0x09,
            0x00,
            0x00,
            0x01,
            (span >> 8) & 0xFF,
            span & 0xFF,
        ]
    )
    crc = crc16_modbus(body)
    crc_h, crc_l = (crc >> 8) & 0xFF, crc & 0xFF
    return body + bytes([crc_h, crc_l])
