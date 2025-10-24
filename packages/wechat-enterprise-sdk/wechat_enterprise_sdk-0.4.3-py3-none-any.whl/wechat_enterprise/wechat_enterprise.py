from pathlib import Path
from typing import List
import requests
import json
from datetime import timedelta, datetime
from requests_toolbelt import MultipartEncoder


class WechatEnterprise:
    """
    企业微信消息推送
    """

    UPLOAD_URL = "https://qyapi.weixin.qq.com/cgi-bin/media/upload"
    SEND_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    GET_USER_URL = "https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={ACCESS_TOKEN}&userid={USERID}"

    def __init__(self, corpid: str, appid: str, corpsecret: str) -> None:
        """
        初始化消息通知应用

        Parameters
        ----------
        corpid : str
            企业 ID
        appid : str
            应用 ID (企业微信网页后台应用管理界面的 AgentId)
        corpsecret : str
            应用 Secret (企业微信网页后台应用管理界面的 Secret)
        """
        self.corpid = corpid
        self.appid = appid
        self.corpsecret = corpsecret
        self.access_token = self.get_access_token()
    
    def get_department_id(self, ID = 0):
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/simplelist?access_token={ACCESS_TOKEN}&id={ID}"
        response = requests.get(url.format(ACCESS_TOKEN = self.access_token, ID=ID))
        return response.json()

    def get_department_userlist(self, department_id = 1):
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token={ACCESS_TOKEN}&department_id={DEPARTMENT_ID}"
        response = requests.get(url.format(ACCESS_TOKEN = self.access_token, DEPARTMENT_ID = department_id))
        return response.json()


    def get_user_info(self, userid):
        """
        userid	是	成员UserID。对应管理端的账号，企业内必须唯一。不区分大小写，长度为1~64个字节, 应用须拥有指定成员的查看权限。
        """
        url = self.GET_USER_URL.format(ACCESS_TOKEN= self.access_token,USERID = userid)
        response = requests.get(url)
        return response.json()

    def upload_file(self, filepath: str, filename: str) -> str:
        """
        上传文件

        Parameters
        ----------
        filepath : str
            本地文件路径
        filename : str
            云端存储的文件名

        Returns
        -------
        str
            上传的文件的 ID
        """
        access_token = self.access_token
        params = {"access_token": access_token, "type": "file"}
        with open(filepath, "rb") as f:
            m = MultipartEncoder(fields={"file": (filename, f, "multipart/form-data")})
            response = requests.post(
                url=self.UPLOAD_URL,
                params=params,
                data=m,
                headers={"Content-Type": m.content_type},
            )
            js = response.json()
            if js["errmsg"] != "ok":
                return ""
            return js["media_id"]

    def send(
        self, msg_type: str, users: List[str], content: str = None, media_id: str = None
    ) -> dict:
        """
        发送消息

        Parameters
        ----------
        msg_type : str
            消息类型

            部分可选值及示例如下
            - ``'text'`` 纯文本
            - ``'markdown'`` Markdown 文本
            - ``'image'`` 图片
            - ``'file'`` 文件

        users : List[str]
            接受消息的的用户账号列表
            例如 ``['ZhangSan','LiSi']``
        content : str, optional
            消息内容, 默认为 ``None``
        media_id : str, optional
            文件 ID, 默认为 ``None``

        Returns
        -------
        dict
        """
        userid_str = "|".join(users)
        access_token = self.access_token
        data = {
            "touser": userid_str,
            "msgtype": msg_type,
            "agentid": self.appid,
            msg_type: {"content": content, "media_id": media_id},
            "safe": 0,
            "enable_id_trans": 1,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800,
        }
        params = {"access_token": access_token}

        response = requests.post(self.SEND_URL, params=params, json=data)
        return response.json()

    def get_access_token(self) -> str:
        cache = Path("./tmp/cache.json")
        cache.parent.mkdir(exist_ok=True)
        if cache.exists():
            try:
                cache_dict: dict = json.loads(cache.read_text())
                if (
                    cache_dict["access_token"]
                    and cache_dict["corpsecret"] == self.corpsecret
                    and datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    <= cache_dict["token_valid_time"]
                ):
                    return cache_dict["access_token"]
            except Exception as e:
                print(f"read cache Failed: {str(e)}")

        access_token = self._get_access_token()
        ## access_token 有效期为 7200秒
        _token_valid_time = (datetime.now() + timedelta(seconds=7190)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        json.dump(
            {
                "corpsecret": self.corpsecret,
                "access_token": access_token,
                "token_valid_time": _token_valid_time,
            },
            cache.open(mode="w"),
        )
        return access_token

    def _get_access_token(self) -> str:  # sourcery skip: raise-specific-error
        """
        获取企业微信应用 token
        Returns
        -------
        str
            企业微信程序 token
        Raises
        ------
        Exception
            当无法获取 token 时
        """
        params = {"corpid": self.corpid, "corpsecret": self.corpsecret}
        response = requests.get(self.TOKEN_URL, params=params)
        js: dict = response.json()
        access_token = js.get("access_token")
        if access_token is None:
            raise Exception("获取 token 失败，请确保相关信息填写正确")
        return access_token

    def send_image(self, image_path: str, users: List[str]) -> bool:
        """
        发送图片给多个用户

        Parameters
        ----------
        image_path : str
            本地图片路径
        users : List[str]
            接受消息的的用户账号列表
        """
        media_id = self.upload_file(image_path, Path(image_path).name)
        return self.send(msg_type="image", users=users, media_id=media_id)

    def send_file(self, file_path: str, users: List[str]) -> bool:
        """
        发送文件给多个用户

        Parameters
        ----------
        file_path : str
            本地文件路径
        users : List[str]
            接受消息的用户账号列表
        """
        media_id = self.upload_file(file_path, Path(file_path).name)
        return self.send(msg_type="file", users=users, media_id=media_id)

    def send_text(self, content: str, users: List[str]) -> bool:
        """
        发送文本消息给多个用户

        Parameters
        ----------
        content : str
            文本内容
        users : List[str]
            接受消息的用户账号列表
        """
        return self.send(msg_type="text", users=users, content=content)

    def send_markdown(self, content: str, users: List[str]) -> bool:
        """
        发送 Markdown 消息给多个用户

        Parameters
        ----------
        content : str
            Markdown 内容
        users : List[str]
            接受消息的用户账号列表
        """
        return self.send(msg_type="markdown", users=users, content=content)

    def get_userid(self, telephone):
        url = "https://qyapi.weixin.qq.com/cgi-bin//user/getuserid?access_token={}".format(self.get_access_token())
        headers = {'Content-Type': 'application/json'}
        body = {'mobile': telephone}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        res = response.json()
        if res['errmsg'] == 'ok':
            return res.get("userid")
        else:
            raise Exception(res['errmsg'])
