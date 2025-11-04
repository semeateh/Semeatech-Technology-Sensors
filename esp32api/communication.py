# communication.py
# 统一封装 4 系列 / 7 系列传感器的串口通信与解析（支持动态“跨度标定”CRC 组帧）
from time import sleep

# ---------- 环境兼容：MicroPython / CPython ----------
try:
    from machine import UART, Pin
    _MICROPY = True
except ImportError:
    _MICROPY = False

# ---------- 工具函数 ----------
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

# ---------- 气体类型映射 ----------
GAS_TYPE_MAPPING_4 = {
    0: "无", 1: "EX", 6: "C3H8", 12: "CL2", 16: "HBr", 18: "AsH3", 20: "Br2", 25: "SiH4",
    26: "无", 27: "无", 28: "无", 29: "无", 30: "无", 35: "无", 36: "无", 37: "C6H6",
    38: "H2O2", 40: "VOC", 2: "CO", 3: "O2", 4: "H2", 5: "CH4", 7: "CO2", 8: "O3",
    9: "H2S", 10: "SO2", 11: "NH3", 13: "ETO", 14: "HCL", 15: "PH3", 17: "HCN",
    19: "HF", 21: "NO", 22: "NO2", 23: "NOX", 24: "CLO2", 31: "THT", 32: "C2H2",
    33: "C2H4", 34: "CH2O", 39: "C2H3CL", 41: "CH3SH", 42: "C4H8"
}
GAS_TYPE_MAPPING_7 = {
    0: "无", 1: "无", 6: "无", 16: "无", 18: "无", 20: "无", 25: "无", 26: "无",
    27: "无", 28: "无", 29: "无", 30: "无", 35: "无", 36: "无", 37: "无", 38: "无",
    2: "CO", 3: "O2", 4: "H2", 5: "CH4", 7: "CO2", 8: "O3", 9: "H2S", 10: "SO2",
    11: "NH3", 12: "CL2", 13: "ETO", 14: "HCL", 15: "PH3", 17: "HCN", 19: "HF",
    21: "NO", 22: "NO2", 23: "NOX", 24: "CLO2", 31: "THT", 32: "C2H2", 33: "C2H4",
    34: "CH2O", 39: "CH3SH", 40: "C2H3CL"
}
def _map_gas(mapping: dict, code: int) -> str:
    return f"{mapping.get(code, '未知')} (code={code})"

# ---------- CRC-16/MODBUS ----------
def crc16_modbus(data: bytes) -> int:
    """
    计算 MODBUS CRC16，初值 0xFFFF，多项式 0xA001，返回 0xHHLL（高8位在高位）
    注意：最终帧中发送顺序为 低字节在前、后跟高字节。
    """
    wcrc = 0xFFFF
    for b in data:
        wcrc ^= b
        for _ in range(8):
            if wcrc & 0x0001:
                wcrc = (wcrc >> 1) ^ 0xA001
            else:
                wcrc >>= 1
    # 这里返回“高字节在高位”的 16 位整值，方便后续分拆
    return ((wcrc & 0xFF) << 8) | (wcrc >> 8)

# ---------- 指令常量（静态查询等仍保留固定帧，以兼容旧主控逻辑） ----------
class FlagCode:
    # 4 系列固定帧（仍可发送）
    F_SENSOR_TYPE1 = "AA 0F 01 C5 80 EE"
    F_SENSOR_NUM2 = "AA 01 01 C1 E0 EE"
    F_SENSOR_MODULE_ZERO3 = "AA 02 01 C1 10 EE"
    F_SENSOR_MODULE_ZERO3_TRUE = "AA 02 01 10 D0 5C EE"
    F_SENSOR_MODULE_CALIBRATION4 = "AA 03 01 C0 80 EE"
    F_SENSOR_MODULE_CALIBRATION4_TRUE = "AA 03 01 10 81 9C EE"
    F_SENSOR_UPDATE_ADDRESS5 = "AA 04 02 82 B1 EE"
    F_SENSOR_UPDATE_ADDRESS5_TRUE = "AA 04 02 10 30 AD EE"
    F_SENSOR_UPDATE_CONCENTRATION6_TRUE = "AA 05 01 10 01 F4 E8 2E EE"

    # 7 系列固定帧（查询）
    S_HEADER = 0x3A
    S_DEFAULT_ID = 0x10
    S_SENSOR_TYPE1 = "3A 10 01 00 00 01 00 00 82 B0"
    S_SENSOR_NUM2 = "3A 10 03 00 00 02 00 00 73 52"   # μg/m³
    S_SENSOR_NUM3 = "3A 10 03 00 02 02 00 00 72 EA"   # ppb
    S_SENSOR_TEMPERATURE4 = "3A 10 03 00 04 01 00 00 82 62"
    S_SENSOR_HUMIDITY5 = "3A 10 03 00 05 01 00 00 83 9E"
    S_SENSOR_PARAMS6 = "3A 10 03 00 00 06 00 00 32 93"
    S_SENSOR_CHECK7 = "3A 10 08 00 0A F9"
    S_SENSOR_ZERO_CALIBRATION8 = "3A 10 07 00 00 01 00 00 82 D6"
    S_SENSOR_SENSITIVITY_CALIBRATION9 = "3A 10 09 00 00 01 00 0A 03 FF"  

# ---------- 解析子串 ----------
def substring_data_4(old_data: str, type_id: int) -> str:
    od = clean_hex(old_data)
    if type_id == 1:
        code = hex_to_decimal(od[6:8])
        return _map_gas(GAS_TYPE_MAPPING_4, code)
    elif type_id == 2:
        return f"{hex_to_decimal(od[8:14])} ppm"
    elif type_id == 3:
        return "模块校零成功" if clean_hex(FlagCode.F_SENSOR_MODULE_ZERO3_TRUE) == od else "模块校零失败"
    elif type_id == 4:
        return "模块标定成功" if clean_hex(FlagCode.F_SENSOR_MODULE_CALIBRATION4_TRUE) == od[:12] else "模块标定失败"
    elif type_id == 5:
        return "地址修改成功" if clean_hex(FlagCode.F_SENSOR_UPDATE_ADDRESS5_TRUE) == od else "地址修改失败"
    elif type_id == 6:
        return "修改模块标气浓度成功" if clean_hex(FlagCode.F_SENSOR_UPDATE_CONCENTRATION6_TRUE) == od else "修改模块标气浓度失败"
    return ""

def substring_data_7(old_data: str, type_id: int) -> str:
    od = clean_hex(old_data)
    if type_id == 1:
        code = hex_to_decimal(od[6:8])
        return _map_gas(GAS_TYPE_MAPPING_7, code)
    elif type_id == 2:
        return f"{hex_to_decimal(od[12:20])}μg/m³"
    elif type_id == 3:
        return f"{hex_to_decimal(od[12:20])}ppb"
    elif type_id == 4:
        return "监测温度为:" + f"{hex_to_decimal(od[12:16])/100:.2f}°C"
    elif type_id == 5:
        return "监测湿度为:" + f"{hex_to_decimal(od[12:16])/100:.2f}%RH"
    elif type_id == 6:
        d1 = hex_to_decimal(od[12:20])
        d2 = hex_to_decimal(od[20:28])
        d3 = hex_to_decimal(od[28:32]) / 100
        d4 = hex_to_decimal(od[32:36]) / 100
        return f"浓度值: {d1} μg/m³, 浓度值: {d2}ppb, 温度值: {d3}°C, 湿度值: {d4}%RH"
    elif type_id == 8:
        return "零点标定返回数值:" + str(hex_to_decimal(od[12:16]))
    elif type_id == 9:
        st = od[6:8]
        flag = "标定成功" if st not in ("01", "02") else ("标定中" if st == "01" else "标定失败")
        return "标定结果:" + flag
    return ""

# ---------- 串口层 ----------
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

class _UARTWrapper:
    def __init__(self, port=2, baudrate=9600, tx=None, rx=None, timeout=300):
        if _MICROPY:
            self.uart = UART(port, baudrate=baudrate, tx=tx or 17, rx=rx or 16, timeout=timeout)
        else:
            self.uart = _MockUART()
    def send_hex_and_read(self, hex_cmd: str, delay_ms: int = 100) -> str:
        self.uart.write(hex_to_bytes(hex_cmd))
        sleep(max(delay_ms, 1) / 1000)
        resp = self.uart.read() or b""
        return bytes_to_hex(resp) if resp else ""

# ---------- 帧构造（动态 CRC） ----------
def build_4_update_span(addr: int, span_ppm: int) -> bytes:
    """
    4 系列：AA | 05 | addr | span_hi | span_lo | CRC_H | CRC_L | EE
    CRC 范围：Byte2~Byte5（05 addr span_hi span_lo）
    """
    addr &= 0xFF
    span = clamp_u16(span_ppm)
    frame_wo_crc = bytes([0x05, addr, (span >> 8) & 0xFF, span & 0xFF])
    crc = crc16_modbus(frame_wo_crc)  # 返回 0xHHLL
    crc_h, crc_l = (crc >> 8) & 0xFF, crc & 0xFF  # 注意：帧内发送顺序为 低字节在前？→ 文档示例给出“高在前字段”，但帧是 H L
    # 文档示例给出 CRC_H / CRC_L 字段顺序，这里按示例字段名写入
    return bytes([0xAA]) + frame_wo_crc + bytes([crc_h, crc_l, 0xEE])

def build_7_sensitivity_cal(dev_id: int, span_ppm: int) -> bytes:
    """
    7 系列：3A | ID | 09 | 00 00 | 01 | D_H | D_L | CRC_H | CRC_L
    CRC 范围：从 0x3A 到数据最后一字节（含 0x3A）
    """
    dev_id &= 0xFF
    span = clamp_u16(span_ppm)
    body = bytes([0x3A, dev_id, 0x09, 0x00, 0x00, 0x01, (span >> 8) & 0xFF, span & 0xFF])
    crc = crc16_modbus(body)
    crc_h, crc_l = (crc >> 8) & 0xFF, crc & 0xFF
    return body + bytes([crc_h, crc_l])

# ---------- 对外 API ----------
class communication:
    """
    对 main.py 的 1~7 菜单保持兼容。
    额外参数：
      - 4 系列默认地址 addr_4 = 0x01
      - 7 系列默认设备码 id_7 = 0x10
    """
    _uart = _UARTWrapper()
    addr_4 = 0x01
    id_7 = 0x10

    @staticmethod
    def init_uart(port=2, baudrate=None, tx=None, rx=None, timeout=300):
        """
        用户自定义初始化 UART 串口接口。
        参数：
            port: 串口号 UART(1) / UART(2)
            baudrate: 波特率（默认 4系=9600，7系=115200）
            tx, rx: 对应引脚号
            timeout: 超时时间
        """
        # 自动匹配波特率（若未指定）
        if baudrate is None:
            baudrate = 9600 if port == 1 else 115200
        communication._uart = _UARTWrapper(port=port, baudrate=baudrate, tx=tx, rx=rx, timeout=timeout)
        print(f"✅ UART 初始化完成: UART({port}), 波特率={baudrate}, TX={tx}, RX={rx}")    
    
    @staticmethod
    def _try_7_then_4(hex_cmd_7: str, hex_cmd_4: str, parse_7, parse_4, parse_id: int):
        rsp7 = communication._uart.send_hex_and_read(hex_cmd_7)
        if rsp7:
            return {"series": 7, "raw": rsp7, "parsed": parse_7(rsp7, parse_id)}
        rsp4 = communication._uart.send_hex_and_read(hex_cmd_4)
        if rsp4:
            return {"series": 4, "raw": rsp4, "parsed": parse_4(rsp4, parse_id)}
        return {"series": None, "raw": "", "parsed": ""}

    @staticmethod
    def getInfo():
        result = communication._try_7_then_4(
            FlagCode.S_SENSOR_TYPE1, FlagCode.F_SENSOR_TYPE1,
            substring_data_7, substring_data_4, 1
        )
        return {"ok": bool(result["series"]), "series": result["series"], "raw": result["raw"], "info": result["parsed"]}

    @staticmethod
    def getSpanValue():
        rsp7a = communication._uart.send_hex_and_read(FlagCode.S_SENSOR_NUM2)
        rsp7b = communication._uart.send_hex_and_read(FlagCode.S_SENSOR_NUM3)
        if rsp7a or rsp7b:
            out = {"series": 7, "raw": {}, "value": {}, "ok": True}
            if rsp7a:
                out["raw"]["μg/m³"] = rsp7a
                out["value"]["μg/m³"] = substring_data_7(rsp7a, 2)
            if rsp7b:
                out["raw"]["ppb"] = rsp7b
                out["value"]["ppb"] = substring_data_7(rsp7b, 3)
            return out
        rsp4 = communication._uart.send_hex_and_read(FlagCode.F_SENSOR_NUM2)
        if rsp4:
            return {"ok": True, "series": 4, "raw": rsp4, "value": substring_data_4(rsp4, 2)}
        return {"ok": False, "series": None, "raw": "", "value": None}

    @staticmethod
    def getReading():
        rsp7 = communication._uart.send_hex_and_read(FlagCode.S_SENSOR_PARAMS6)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "parsed": substring_data_7(rsp7, 6)}
        rsp4 = communication._uart.send_hex_and_read(FlagCode.F_SENSOR_NUM2)
        if rsp4:
            return {"ok": True, "series": 4, "raw": rsp4, "parsed": substring_data_4(rsp4, 2)}
        return {"ok": False, "series": None, "raw": "", "parsed": ""}

    @staticmethod
    def zeroCal():
        rsp7 = communication._uart.send_hex_and_read(FlagCode.S_SENSOR_ZERO_CALIBRATION8)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "result": substring_data_7(rsp7, 8)}
        rsp4 = communication._uart.send_hex_and_read(FlagCode.F_SENSOR_MODULE_ZERO3)
        if rsp4:
            return {"ok": True, "series": 4, "raw": rsp4, "result": substring_data_4(rsp4, 3)}
        return {"ok": False, "series": None, "raw": "", "result": "无返回"}

    @staticmethod
    def spanCal(spanValue: int, *, prefer="7-first"):
        """
        任意浓度跨度标定（单位 PPM）：
          - 7 系列：灵敏度标定 (功能码 0x09)，数据 2Bytes，高位在前；CRC 从 0x3A 开始算到数据尾。
          - 4 系列：修改标准气体浓度（命令 0x05），CRC 覆盖 Byte2~Byte5。
        prefer: "7-first" / "4-first"
        """
        span_ppm = clamp_u16(spanValue)
        id7 = communication.id_7 & 0xFF
        addr4 = communication.addr_4 & 0xFF

        frame7 = build_7_sensitivity_cal(id7, span_ppm)
        frame4 = build_4_update_span(addr4, span_ppm)

        def send7():
            return communication._uart.send_hex_and_read(bytes_to_hex(frame7), delay_ms=150)
        def send4():
            return communication._uart.send_hex_and_read(bytes_to_hex(frame4), delay_ms=150)

        rsp7 = rsp4 = ""
        if prefer == "4-first":
            rsp4 = send4()
            if "EE" not in rsp4 and rsp4 == "":
                rsp7 = send7()
        else:
            rsp7 = send7()
            if "EE" not in rsp7 and rsp7 == "":
                rsp4 = send4()

        out = {"ok": False, "series": None, "request": {"7": bytes_to_hex(frame7), "4": bytes_to_hex(frame4)}, "response": {}}

        if rsp7:
            out["response"]["7"] = rsp7
            # 7 系列标定结果（0=成功、1=标定中、2=失败），返回帧简写：3A 10 09 <status> CRC
            out["series"] = 7
            out["ok"] = (" 00 " in f" {rsp7} ") or (" 标定成功" in substring_data_7(rsp7, 9))
            out["result"] = substring_data_7(rsp7, 9)

        if rsp4:
            out["response"]["4"] = rsp4
            out["series"] = out["series"] or 4
            # 4 系列成功：AA 05 01 10 <span_hi> <span_lo> CRC_H CRC_L EE
            if " AA 05 " in f" {rsp4} " and " 10 " in f" {rsp4} "[9:14]:
                out["ok"] = True
            if not out.get("result"):
                out["result"] = substring_data_4(rsp4, 6)

        if not rsp7 and not rsp4:
            out["note"] = "无设备应答，检查接线/电源/串口参数"

        # 附加说明
        out["note2"] = f"span={span_ppm} ppm, id7=0x{id7:02X}, addr4=0x{addr4:02X}"
        return out

    @staticmethod
    def getTemp():
        rsp7 = communication._uart.send_hex_and_read(FlagCode.S_SENSOR_TEMPERATURE4)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "value": substring_data_7(rsp7, 4)}
        return {"ok": False, "series": None, "raw": "", "value": None}

    @staticmethod
    def getHumi():
        rsp7 = communication._uart.send_hex_and_read(FlagCode.S_SENSOR_HUMIDITY5)
        if rsp7:
            return {"ok": True, "series": 7, "raw": rsp7, "value": substring_data_7(rsp7, 5)}
        return {"ok": False, "series": None, "raw": "", "value": None}




