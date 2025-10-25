from wechat_enterprise import WechatEnterprise

we = WechatEnterprise(
    corpid="ww2563f***********",  # 企业 ID
    appid="100****3",  # 企业应用 ID
    corpsecret="*********************",  # 企业应用 Secret
)

receivers = ["ZhengZheng", "DaZhengGe"]
# 发送 文本
we.send_text("来息 somenzz 的消息", receivers)
# 发送 Markdown
we.send_markdown("# Markdown", receivers)
# 发送图片
we.send_image("/Users/aaron/Downloads/images.jpeg", receivers)
# 发送文件
we.send_file("./wechat_enterprise.py", receivers)
