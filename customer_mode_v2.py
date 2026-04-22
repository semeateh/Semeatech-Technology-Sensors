"""
客户模式 V2

目标：
1. 将“函数菜单”升级为“状态首页 + 向导流程”。
2. 自动检测 UART 参数并保存配置，减少重复设置。
3. 在不改变客户使用习惯的前提下，底层统一切换到 SensorClient。
"""

from time import sleep

try:
    import ujson as json
except ImportError:
    import json

try:
    import uos as os
except ImportError:
    import os

try:
    from esp32api import SensorClient
except ImportError:
    from esp32api.client import SensorClient


CONFIG_FILE = "customer_mode_v2_config.json"
DEFAULT_CONFIG = {
    "port": 2,
    "baudrate": 115200,
    "tx": 17,
    "rx": 16,
    "addr_4": 1,
    "id_7": 16,
}
DETECT_CANDIDATES = (
    {"port": 2, "baudrate": 115200, "tx": 17, "rx": 16},
    {"port": 1, "baudrate": 9600, "tx": 17, "rx": 16},
)


# 当前客户模式正在使用的 SDK 客户端实例。
# 这样可以在不改变页面交互的前提下，把底层统一切换到 SensorClient。
_CLIENT = None


def _safe_print(message=""):
    try:
        print(message)
    except Exception:
        pass


def _file_exists(path):
    try:
        return path in os.listdir()
    except Exception:
        try:
            with open(path, "r"):
                return True
        except Exception:
            return False


def load_config():
    if not _file_exists(CONFIG_FILE):
        return None

    try:
        with open(CONFIG_FILE, "r") as fp:
            data = json.load(fp)
    except Exception as exc:
        _safe_print("检测到配置文件，但读取失败。")
        _safe_print("原因: %s" % exc)
        return None

    merged = dict(DEFAULT_CONFIG)
    merged.update(data or {})
    return normalize_config(merged)


def save_config(config):
    data = normalize_config(config)
    with open(CONFIG_FILE, "w") as fp:
        json.dump(data, fp)


def default_baudrate_for_port(port):
    return 9600 if int(port) == 1 else 115200


def normalize_config(config):
    normalized = dict(DEFAULT_CONFIG)
    normalized.update(config or {})
    normalized["port"] = int(normalized.get("port", DEFAULT_CONFIG["port"]))
    normalized["baudrate"] = default_baudrate_for_port(normalized["port"])
    normalized["tx"] = int(normalized.get("tx", DEFAULT_CONFIG["tx"]))
    normalized["rx"] = int(normalized.get("rx", DEFAULT_CONFIG["rx"]))
    normalized["addr_4"] = int(normalized.get("addr_4", DEFAULT_CONFIG["addr_4"]))
    normalized["id_7"] = int(normalized.get("id_7", DEFAULT_CONFIG["id_7"]))
    return normalized


def apply_config(config):
    global _CLIENT
    normalized = normalize_config(config)
    # 每次应用配置时，都重建一个新的 SensorClient。
    # 这样客户模式后续所有操作都通过统一的 SDK 实例完成。
    _CLIENT = SensorClient(
        port=normalized["port"],
        baudrate=normalized["baudrate"],
        tx=normalized["tx"],
        rx=normalized["rx"],
        addr_4=normalized["addr_4"],
        id_7=normalized["id_7"],
    )


def get_client():
    # 所有页面动作都通过这里获取当前生效的 SDK 客户端，
    # 避免不同页面各自初始化串口，造成状态不一致。
    if _CLIENT is None:
        raise RuntimeError("当前尚未完成串口初始化，请先执行配置流程。")
    return _CLIENT


def ask_text(prompt, default=None):
    suffix = ""
    if default is not None:
        suffix = " [默认 %s]" % default
    try:
        value = input("%s%s: " % (prompt, suffix)).strip()
    except Exception:
        value = ""
    if value == "" and default is not None:
        return str(default)
    return value


def ask_int(prompt, default=None, minimum=None, maximum=None):
    while True:
        raw = ask_text(prompt, default=default)
        if raw == "" and default is None:
            return None

        try:
            value = int(raw)
        except Exception:
            _safe_print("请输入整数。")
            continue

        if minimum is not None and value < minimum:
            _safe_print("输入值不能小于 %s。" % minimum)
            continue
        if maximum is not None and value > maximum:
            _safe_print("输入值不能大于 %s。" % maximum)
            continue
        return value


def ask_yes_no(prompt, default=True):
    default_hint = "Y/n" if default else "y/N"
    raw = ask_text("%s (%s)" % (prompt, default_hint), default="")
    if raw == "":
        return default
    raw = raw.lower()
    return raw in ("y", "yes", "1", "是")


def format_value(value):
    if isinstance(value, dict):
        items = []
        for key in sorted(value.keys()):
            items.append("%s=%s" % (key, value[key]))
        return "，".join(items)
    return str(value)


def series_name(series):
    if series == 4:
        return "4 系列"
    if series == 7:
        return "7 系列"
    return "未知系列"


def update_config_by_info(config, info):
    if info and info.get("ok"):
        config["detected_series"] = info.get("series")
        config["last_info"] = info.get("info")


def print_title():
    _safe_print("")
    _safe_print("==============================================")
    _safe_print(" Sematech 传感器客户模式 V2")
    _safe_print(" 上电即查看设备状态，校准流程改为向导式操作")
    _safe_print("==============================================")


def print_config_summary(config):
    _safe_print("")
    _safe_print("当前连接参数:")
    _safe_print("  串口: UART(%s)" % config.get("port"))
    _safe_print("  波特率: %s" % config.get("baudrate"))
    _safe_print("  TX/RX: %s / %s" % (config.get("tx"), config.get("rx")))
    _safe_print("  4系列地址: %s" % config.get("addr_4"))
    _safe_print("  7系列ID: %s" % config.get("id_7"))


def explain_failure():
    _safe_print("")
    _safe_print("设备没有正常返回，建议按顺序检查:")
    _safe_print("1. 传感器是否已经上电")
    _safe_print("2. TX 和 RX 是否接反")
    _safe_print("3. 波特率是否匹配")
    _safe_print("4. 是否使用了正确的 UART 口")
    _safe_print("5. 传感器是否确实为 UART 协议")


def print_result(title, result):
    _safe_print("")
    _safe_print("---- %s ----" % title)
    if not result:
        _safe_print("未收到有效结果。")
        explain_failure()
        return

    ok = result.get("ok")
    _safe_print("执行状态: %s" % ("成功" if ok else "失败"))

    if "series" in result and result.get("series"):
        _safe_print("识别系列: %s" % series_name(result.get("series")))
    if "info" in result and result.get("info"):
        _safe_print("模块信息: %s" % result.get("info"))
    if "parsed" in result and result.get("parsed"):
        _safe_print("解析结果: %s" % result.get("parsed"))
    if "value" in result and result.get("value") not in (None, ""):
        _safe_print("数值结果: %s" % format_value(result.get("value")))
    if "result" in result and result.get("result"):
        _safe_print("返回结果: %s" % result.get("result"))
    if "note" in result and result.get("note"):
        _safe_print("提示: %s" % result.get("note"))
    if "note2" in result and result.get("note2"):
        _safe_print("附加说明: %s" % result.get("note2"))

    if not ok:
        explain_failure()


def detect_once(candidate):
    config = dict(DEFAULT_CONFIG)
    config.update(candidate)
    apply_config(config)

    _safe_print("")
    _safe_print(
        "正在尝试: UART(%s), 波特率=%s, TX=%s, RX=%s"
        % (config["port"], config["baudrate"], config["tx"], config["rx"])
    )

    info = get_client().getInfo()
    if info.get("ok"):
        update_config_by_info(config, info)
        return config, info
    return None, info


def auto_detect():
    _safe_print("")
    _safe_print("开始自动检测设备，请稍候...")
    for candidate in DETECT_CANDIDATES:
        config, info = detect_once(candidate)
        if config:
            _safe_print("自动检测成功。")
            print_result("设备识别", info)
            return config

    _safe_print("自动检测未成功。")
    explain_failure()
    return None


def manual_setup():
    _safe_print("")
    _safe_print("进入高级设置。以下参数仅建议工程人员修改。")
    config = normalize_config(DEFAULT_CONFIG)
    config["port"] = ask_int("UART 串口号", default=config["port"], minimum=1, maximum=2)
    config["baudrate"] = default_baudrate_for_port(config["port"])
    _safe_print("当前串口对应的固定波特率为: %s" % config["baudrate"])
    config["tx"] = ask_int("TX 引脚", default=config["tx"], minimum=0, maximum=99)
    config["rx"] = ask_int("RX 引脚", default=config["rx"], minimum=0, maximum=99)
    config["addr_4"] = ask_int("4系列地址", default=config["addr_4"], minimum=0, maximum=255)
    config["id_7"] = ask_int("7系列设备ID", default=config["id_7"], minimum=0, maximum=255)
    config = normalize_config(config)

    apply_config(config)
    info = get_client().getInfo()
    print_result("高级设置后的设备识别", info)

    if info.get("ok"):
        update_config_by_info(config, info)
        return config
    return None


def ensure_config():
    config = load_config()
    if config:
        _safe_print("已读取上次保存的配置。")
        apply_config(config)
        info = get_client().getInfo()
        if info.get("ok"):
            update_config_by_info(config, info)
            save_config(config)
            return config

        _safe_print("保存的配置未能连接到设备，准备重新检测。")
        explain_failure()

    config = auto_detect()
    if config:
        save_config(config)
        return config

    if ask_yes_no("是否进入高级设置", default=True):
        config = manual_setup()
        if config:
            save_config(config)
            return config

    return None


def collect_snapshot(config):
    client = get_client()
    info = client.getInfo()
    snapshot = {
        "connected": bool(info.get("ok")),
        "series": info.get("series"),
        "info": info.get("info"),
        "reading": "",
        "temp": "",
        "humi": "",
    }

    if not snapshot["connected"]:
        return snapshot

    update_config_by_info(config, info)

    reading = client.getReading()
    if reading.get("ok"):
        snapshot["reading"] = reading.get("parsed") or format_value(reading.get("value"))

    temp = client.getTemp()
    if temp.get("ok"):
        snapshot["temp"] = temp.get("value")

    humi = client.getHumi()
    if humi.get("ok"):
        snapshot["humi"] = humi.get("value")

    return snapshot


def print_snapshot(snapshot, title="设备状态首页"):
    _safe_print("")
    _safe_print("============== %s ==============" % title)
    if not snapshot.get("connected"):
        _safe_print("连接状态: 未连接")
        _safe_print("建议进入“连接设置”重新识别设备。")
        return

    _safe_print("连接状态: 已连接")
    _safe_print("设备系列: %s" % series_name(snapshot.get("series")))
    _safe_print("识别结果: %s" % (snapshot.get("info") or "未识别到型号"))
    _safe_print("当前读数: %s" % (snapshot.get("reading") or "暂无数据"))

    if snapshot.get("temp") or snapshot.get("humi"):
        _safe_print("温湿度: %s | %s" % (
            snapshot.get("temp") or "温度暂无数据",
            snapshot.get("humi") or "湿度暂无数据",
        ))
    else:
        _safe_print("温湿度: 当前设备未提供或暂未读取到")


def action_device_details(config):
    client = get_client()
    info = client.getInfo()
    span = client.getSpanValue()
    update_config_by_info(config, info)

    print_result("设备信息", info)
    print_result("量程信息", span)


def action_live_monitor(config):
    _safe_print("")
    _safe_print("进入连续检测。运行过程中可使用 Ctrl+C 提前结束。")
    interval_sec = ask_int("刷新间隔（秒）", default=2, minimum=1, maximum=60)
    rounds = ask_int("连续检测次数", default=10, minimum=1, maximum=999)

    try:
        for index in range(1, rounds + 1):
            snapshot = collect_snapshot(config)
            print_snapshot(snapshot, title="连续检测 %s/%s" % (index, rounds))
            if not snapshot.get("connected"):
                explain_failure()
                break
            if index < rounds:
                sleep(interval_sec)
    except KeyboardInterrupt:
        _safe_print("")
        _safe_print("已手动结束连续检测。")


def action_zero_cal():
    _safe_print("")
    _safe_print("校零向导")
    _safe_print("1. 确认传感器已经稳定工作。")
    _safe_print("2. 确认当前处于洁净空气环境。")
    _safe_print("3. 确认周围没有待测目标气体。")

    if not ask_yes_no("以上条件都满足，开始校零", default=False):
        _safe_print("已取消校零。")
        return

    print_result("校零结果", get_client().zeroCal())


def action_span_cal():
    _safe_print("")
    _safe_print("标定向导")
    _safe_print("1. 先接入标准气体。")
    _safe_print("2. 等待读数稳定后再开始。")
    _safe_print("3. 输入这瓶标准气体的标称浓度。")

    span = ask_int("请输入标准气体浓度 PPM", default=250, minimum=0, maximum=65535)
    if span is None:
        _safe_print("未输入浓度，已取消。")
        return

    _safe_print("本次将按 %s PPM 执行标定。" % span)
    if not ask_yes_no("确认开始标定", default=False):
        _safe_print("已取消标定。")
        return

    print_result("标定结果", get_client().spanCal(span, prefer="7-first"))


def action_reconfigure(current_config):
    _safe_print("")
    _safe_print("连接设置")
    _safe_print("1. 查看当前连接参数")
    _safe_print("2. 自动重新识别设备")
    _safe_print("3. 进入高级设置")
    _safe_print("0. 返回首页")

    while True:
        choice = ask_text("请选择设置项", default="1")
        if choice == "1":
            print_config_summary(normalize_config(current_config))
            return None
        if choice == "2":
            config = auto_detect()
            if config:
                save_config(config)
                _safe_print("新配置已保存。")
                print_config_summary(config)
                return config
            _safe_print("自动识别失败，继续使用当前配置。")
            return None
        if choice == "3":
            config = manual_setup()
            if config:
                save_config(config)
                _safe_print("高级设置已保存。")
                print_config_summary(config)
                return config
            _safe_print("高级设置未完成，继续使用当前配置。")
            return None
        if choice == "0":
            return None
        _safe_print("无效编号，请重新输入。")


def show_menu():
    _safe_print("")
    _safe_print("请选择操作:")
    _safe_print("1. 开始连续检测")
    _safe_print("2. 查看设备详情")
    _safe_print("3. 校零向导")
    _safe_print("4. 标定向导")
    _safe_print("5. 连接设置")
    _safe_print("0. 退出")


def run():
    print_title()
    config = ensure_config()
    if not config:
        _safe_print("")
        _safe_print("暂未完成配置，程序结束。")
        return

    _safe_print("")
    _safe_print("设备准备完成，首页将自动刷新当前状态。")

    while True:
        snapshot = collect_snapshot(config)
        print_snapshot(snapshot)
        if snapshot.get("info"):
            config["last_info"] = snapshot.get("info")

        show_menu()
        choice = ask_text("请输入编号", default="1").upper()

        if choice == "1":
            action_live_monitor(config)
        elif choice == "2":
            action_device_details(config)
        elif choice == "3":
            action_zero_cal()
        elif choice == "4":
            action_span_cal()
        elif choice == "5":
            new_config = action_reconfigure(config)
            if new_config:
                config = new_config
                apply_config(config)
        elif choice == "0":
            _safe_print("已退出客户模式。")
            break
        else:
            _safe_print("无效编号，请重新输入。")
