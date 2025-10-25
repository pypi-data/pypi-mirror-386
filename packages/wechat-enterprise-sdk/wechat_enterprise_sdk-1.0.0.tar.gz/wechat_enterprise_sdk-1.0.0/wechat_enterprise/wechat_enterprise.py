import requests
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from requests import Session, Response
from datetime import timedelta, datetime

# 1. 可维护性：自定义异常类
class WechatEnterpriseError(Exception):
    """企业微信 API 请求异常"""
    def __init__(self, message: str, errcode: int = -1):
        super().__init__(f"[Errcode: {errcode}] {message}")
        self.errcode = errcode

class WechatEnterprise:
    """
    企业微信消息推送

    优化点:
    1. 使用 requests.Session 进行连接复用。
    2. 使用实例内存缓存管理 access_token，替代文件缓存，更通用健壮。
    3. 集中化 API 请求和错误处理 (_api_get, _api_post, _handle_api_response)。
    4. 移除 requests_toolbelt 依赖，简化文件上传。
    5. 明确的异常抛出 (WechatEnterpriseError)。
    """

    # 1. 可读性：统一管理 API 端点
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    TOKEN_URL = f"{BASE_URL}/gettoken"
    SEND_URL = f"{BASE_URL}/message/send"
    UPLOAD_URL = f"{BASE_URL}/media/upload"
    GET_USER_URL = f"{BASE_URL}/user/get"
    GET_USERID_URL = f"{BASE_URL}/user/getuserid"
    DEPT_SIMPLELIST_URL = f"{BASE_URL}/department/simplelist"
    USER_SIMPLELIST_URL = f"{BASE_URL}/user/simplelist"

    # 2. 易用性：Token 缓存的过期时间 buffer（秒）
    TOKEN_EXPIRATION_BUFFER = 60

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

        # 2. 可维护性：使用 Session 管理 HTTP 连接
        self.session: Session = requests.Session()

        # 3. 易用性：实例内存缓存
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _handle_api_response(self, response: Response) -> Dict[str, Any]:
        """
        私有辅助方法：集中处理 API 响应和错误。
        """
        # 抛出 HTTP 级别错误 (4xx, 5xx)
        response.raise_for_status()

        try:
            js: Dict[str, Any] = response.json()
        except requests.exceptions.JSONDecodeError:
            raise WechatEnterpriseError(f"API 响应非 JSON 格式: {response.text}", -1)

        # 检查企业微信 API 业务错误
        errcode = js.get("errcode", 0)
        errmsg = js.get("errmsg", "ok")

        if errcode != 0:
            raise WechatEnterpriseError(errmsg, errcode)

        return js

    def _api_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        私有辅助方法：封装带 token 的 GET 请求。
        """
        # 确保 params 是一个字典
        if params is None:
            params = {}

        # 自动注入 access_token
        params_with_token = {"access_token": self.get_access_token(), **params}

        response = self.session.get(url, params=params_with_token)
        return self._handle_api_response(response)

    def _api_post(self, url: str,
                  params: Optional[Dict[str, Any]] = None,
                  json_data: Optional[Dict[str, Any]] = None,
                  files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        私有辅助方法：封装带 token 的 POST 请求。
        access_token 放在 URL query params 中。
        """
        # POST 请求的 token 默认在 query params
        query_params = {"access_token": self.get_access_token()}
        if params:
            query_params.update(params)

        response = self.session.post(url, params=query_params, json=json_data, files=files)
        return self._handle_api_response(response)

    def _fetch_access_token(self) -> str:
        """
        私有辅助方法：从服务器获取新 token 并更新缓存。
        """
        params = {"corpid": self.corpid, "corpsecret": self.corpsecret}

        try:
            response = self.session.get(self.TOKEN_URL, params=params)
            js = self._handle_api_response(response)
        except Exception as e:
            # 获取 token 失败是致命错误，应明确抛出
            raise WechatEnterpriseError(f"获取 token 失败，请确保 corpid 和 corpsecret 正确: {e}", -1)

        access_token = js["access_token"]
        # API 返回的有效期，单位秒
        expires_in = js.get("expires_in", 7200)

        # 3. 易用性：更新实例缓存
        self._access_token = access_token
        self._token_expires_at = datetime.now() + timedelta(
            seconds=expires_in - self.TOKEN_EXPIRATION_BUFFER
        )

        return access_token

    def get_access_token(self) -> str:
        """
        获取企业微信应用 token (带实例缓存)。
        """
        # 3. 易用性：检查内存缓存
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        # 缓存无效，重新获取
        return self._fetch_access_token()

    def get_department_id(self, dept_id: int = 0) -> Dict[str, Any]:
        """获取部门列表"""
        return self._api_get(self.DEPT_SIMPLELIST_URL, params={"id": dept_id})

    def get_department_userlist(self, department_id: int = 1) -> Dict[str, Any]:
        """获取部门成员简易列表"""
        return self._api_get(self.USER_SIMPLELIST_URL, params={"department_id": department_id})

    def get_user_info(self, userid: str) -> Dict[str, Any]:
        """
        获取成员信息
        userid: 成员UserID。对应管理端的账号。
        """
        return self._api_get(self.GET_USER_URL, params={"userid": userid})

    def get_userid(self, telephone: str) -> Optional[str]:
        """
        根据手机号获取成员 userid
        """
        response_json = self._api_post(self.GET_USERID_URL, json_data={"mobile": telephone})
        return response_json.get("userid")

    def upload_file(self, filepath: str, filename: str, file_type: str = "file") -> str:
        """
        上传文件

        Parameters
        ----------
        filepath : str
            本地文件路径
        filename : str
            在企业微信中显示的文件名
        file_type : str, optional
            文件类型 (file, image, voice, video), 默认为 "file"

        Returns
        -------
        str
            上传的文件的 media_id

        Raises
        ------
        WechatEnterpriseError
            如果上传失败
        """
        # 4. 可读性：简化文件上传，移除 requests_toolbelt
        params = {"type": file_type}
        try:
            with open(filepath, "rb") as f:
                # 'file' 是 API 要求的字段名
                files = {"file": (filename, f, "application/octet-stream")}
                response_json = self._api_post(self.UPLOAD_URL, params=params, files=files)

            # _handle_api_response 已确保 "errcode" 为 0
            return response_json["media_id"]

        except FileNotFoundError:
            raise WechatEnterpriseError(f"文件未找到: {filepath}", -1)
        except Exception as e:
            raise WechatEnterpriseError(f"文件上传失败: {e}", -1)

    def _send(self, msg_type: str, users: List[str],
              content: Optional[str] = None,
              media_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发送消息的私有核心方法

        Raises
        ------
        WechatEnterpriseError
            如果发送失败
        ValueError
            如果消息类型不支持
        """
        userid_str = "|".join(users)

        # 基础消息体
        data: Dict[str, Any] = {
            "touser": userid_str,
            "msgtype": msg_type,
            "agentid": self.appid,
            "safe": 0,
            "enable_id_trans": 1,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800,
        }

        # 4. 可读性：根据类型动态构建消息内容
        if msg_type == "text":
            if content is None:
                raise ValueError("文本消息 'content' 不能为空")
            data[msg_type] = {"content": content}
        elif msg_type == "markdown":
            if content is None:
                raise ValueError("Markdown 消息 'content' 不能为空")
            data[msg_type] = {"content": content}
        elif msg_type in ("image", "file", "voice", "video"):
            if media_id is None:
                raise ValueError(f"{msg_type} 消息 'media_id' 不能为空")
            data[msg_type] = {"media_id": media_id}
        else:
            raise ValueError(f"不支持的消息类型: {msg_type}")

        return self._api_post(self.SEND_URL, json_data=data)

    def send_image(self, image_path: str, users: List[str]) -> Dict[str, Any]:
        """
        发送图片给多个用户

        Returns
        -------
        dict
            API 响应
        """
        media_id = self.upload_file(image_path, Path(image_path).name, file_type="image")
        return self._send(msg_type="image", users=users, media_id=media_id)

    def send_file(self, file_path: str, users: List[str]) -> Dict[str, Any]:
        """
        发送文件给多个用户

        Returns
        -------
        dict
            API 响应
        """
        media_id = self.upload_file(file_path, Path(file_path).name, file_type="file")
        return self._send(msg_type="file", users=users, media_id=media_id)

    def send_text(self, content: str, users: List[str]) -> Dict[str, Any]:
        """
        发送文本消息给多个用户

        Returns
        -------
        dict
            API 响应
        """
        return self._send(msg_type="text", users=users, content=content)

    def send_markdown(self, content: str, users: List[str]) -> Dict[str, Any]:
        """
        发送 Markdown 消息给多个用户

        Returns
        -------
        dict
            API 响应
        """
        return self._send(msg_type="markdown", users=users, content=content)

