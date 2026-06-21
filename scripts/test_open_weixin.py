from pyweixin.WeChatTools import Navigator

try:
    window = Navigator.open_weixin(is_maximize=False)
    print("OK", window.class_name())
except Exception as exc:
    print("FAIL", type(exc).__name__, exc)