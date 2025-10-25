# 用 Python 发送企业微信消息

支持发送：
- 文本
- 文件
- 图片
- MarkDown

## 安装
```sh
pip install wechat-enterprise-sdk
```

## 使用

获取的 access_token 会保存在内存缓存里面，避免高频率获取 access_token。

```python

from wechat_enterprise import WechatEnterprise

if __name__ == '__main__':
    # 替换为你自己的企业微信凭证
    CORP_ID = "YOUR_CORP_ID"
    APP_ID = "YOUR_APP_ID"
    CORP_SECRET = "YOUR_CORP_SECRET"
    
    # 接收消息的用户账号
    USER_LIST = ["ZhangSan", "LiSi"]
    
    try:
        # 1. 初始化
        wechat = WechatEnterprise(corpid=CORP_ID, appid=APP_ID, corpsecret=CORP_SECRET)
        
        # 2. 发送文本
        print("正在发送文本消息...")
        response_text = wechat.send_text("这是一条来自优化后代码的测试文本消息。", USER_LIST)
        print(f"发送成功: {response_text}")

        # 3. 发送 Markdown
        print("\n正在发送 Markdown 消息...")
        markdown_content = (
            "**Markdown 测试**\n"
            "> 引用内容\n"
            "包含 `code` 和 [链接](https://work.weixin.qq.com/api/doc/90000/90135/90236)"
        )
        response_md = wechat.send_markdown(markdown_content, USER_LIST)
        print(f"发送成功: {response_md}")
        
        # 4. 发送文件 (示例)
        # print("\n正在发送文件...")
        # # 创建一个临时文件用于测试
        # test_file_path = "./test_upload.txt"
        # with open(test_file_path, "w") as f:
        #     f.write("这是一个测试上传的文件。")
            
        # response_file = wechat.send_file(test_file_path, USER_LIST)
        # print(f"发送成功: {response_file}")

        # 5. 获取用户信息 (示例)
        print(f"\n正在获取用户 {USER_LIST[0]} 的信息...")
        user_info = wechat.get_user_info(USER_LIST[0])
        print(f"获取成功: {user_info.get('name')}")
        
    except WechatEnterpriseError as e:
        print(f"企业微信 API 出错: {e}")
    except Exception as e:
        print(f"发生其他错误: {e}")


#接收者 ID，在企业微信通讯录中查看
receivers = ["ZhengZheng", "DaZhengGe"]
# 发送 文本
we.send_text("来息 somenzz 的消息", receivers)
# 发送 Markdown
we.send_markdown("# Markdown", receivers)
# 发送图片
we.send_image("/Users/aaron/Downloads/images.jpeg", receivers)
# 发送文件
we.send_file("./wechat_enterprise.py", receivers)
# 根据手机号获取企业微信账号：
userid = we.get_userid("138********")
we.send_text("hello",[userid,])
```

## todo

添加企业微信的其他实用功能

## 联系我

添加微信 「somenzz-enjoy」 备注 「github」

个人公众号 「Python七号」，微信搜一搜关注。
