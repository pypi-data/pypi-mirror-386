import requests
import json 
from pathlib import Path
from typing import List, Dict, Any, Optional
from requests import Session, Response
from datetime import timedelta, datetime

class WechatEnterpriseError(Exception):
    """企业微信 API 请求异常"""
    def __init__(self, message: str, errcode: int = -1):
        super().__init__(f"[Errcode: {errcode}] {message}")
        self.errcode = errcode

class WechatEnterprise:
    """
    企业微信消息推送 (支持内存缓存与文件缓存)
    """

    # (API 端点保持不变)
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    TOKEN_URL = f"{BASE_URL}/gettoken"
    SEND_URL = f"{BASE_URL}/message/send"
    UPLOAD_URL = f"{BASE_URL}/media/upload"
    GET_USER_URL = f"{BASE_URL}/user/get"
    GET_USERID_URL = f"{BASE_URL}/user/getuserid"
    DEPT_SIMPLELIST_URL = f"{BASE_URL}/department/simplelist"
    USER_SIMPLELIST_URL = f"{BASE_URL}/user/simplelist"

    TOKEN_EXPIRATION_BUFFER = 60

    def __init__(self,
                 corpid: str,
                 appid: str,
                 corpsecret: str,
                 cache_path: Optional[Path] = Path("./we_token_cache.json")
                 ) -> None:
        """
        初始化消息通知应用

        Parameters
        ----------
        corpid : str
            企业 ID
        appid : str
            应用 ID (AgentId)
        corpsecret : str
            应用 Secret
        cache_path : Optional[Path], optional
            Token 文件缓存路径。
            默认为 './we_token_cache.json'。
            如果设为 None，则禁用文件缓存。
        """
        self.corpid = corpid
        self.appid = appid
        self.corpsecret = corpsecret

        self.session: Session = requests.Session()

        # 2. 内存缓存 (一级缓存)
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # 3. 文件缓存 (二级缓存) 路径
        self.cache_path: Optional[Path] = cache_path

    def _handle_api_response(self, response: Response) -> Dict[str, Any]:
        """私有辅助方法：集中处理 API 响应和错误。"""
        response.raise_for_status()
        try:
            js: Dict[str, Any] = response.json()
        except requests.exceptions.JSONDecodeError:
            raise WechatEnterpriseError(f"API 响应非 JSON 格式: {response.text}", -1)

        errcode = js.get("errcode", 0)
        errmsg = js.get("errmsg", "ok")
        if errcode != 0:
            raise WechatEnterpriseError(errmsg, errcode)
        return js

    def _api_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """私有辅助方法：封装带 token 的 GET 请求。"""
        if params is None:
            params = {}
        params_with_token = {"access_token": self.get_access_token(), **params}
        response = self.session.get(url, params=params_with_token)
        return self._handle_api_response(response)

    def _api_post(self, url: str,
                  params: Optional[Dict[str, Any]] = None,
                  json_data: Optional[Dict[str, Any]] = None,
                  files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """私有辅助方法：封装带 token 的 POST 请求。"""
        query_params = {"access_token": self.get_access_token()}
        if params:
            query_params.update(params)
        response = self.session.post(url, params=query_params, json=json_data, files=files)
        return self._handle_api_response(response)

    # 4. 新增：从文件加载 Token
    def _load_token_from_file(self) -> Optional[str]:
        """
        私有辅助方法：尝试从文件缓存加载 token。
        如果加载成功，会更新内存缓存。
        """
        if not self.cache_path or not self.cache_path.exists():
            return None

        try:
            cache_data = json.loads(self.cache_path.read_text())

            # 必须检查 secret，防止多个应用实例误用缓存
            if cache_data.get("corpsecret") != self.corpsecret:
                return None

            expires_at_ts = cache_data.get("expires_at_timestamp", 0)
            real_expires_at_dt = datetime.fromtimestamp(expires_at_ts)

            # 检查是否过期 (使用 buffer)
            buffered_expires_at_dt = real_expires_at_dt - timedelta(seconds=self.TOKEN_EXPIRATION_BUFFER)

            if datetime.now() < buffered_expires_at_dt:
                token = cache_data.get("access_token")
                if token:
                    # 加载到内存缓存
                    self._access_token = token
                    self._token_expires_at = buffered_expires_at_dt
                    return token

        except (json.JSONDecodeError, IOError, TypeError) as e:
            # 文件损坏、不可读或时间戳格式错误
            print(f"Warning: 无法读取 token 缓存文件, 将重新获取. 错误: {e}")

        return None

    # 5. 新增：保存 Token 到文件
    def _save_token_to_file(self, token: str, real_expires_at_dt: datetime):
        """
        私有辅助方法：将 token 保存到文件。
        """
        if not self.cache_path:
            return

        try:
            # 确保目录存在
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            cache_data = {
                "corpsecret": self.corpsecret,
                "access_token": token,
                # 存储为 Unix 时间戳，更通用
                "expires_at_timestamp": real_expires_at_dt.timestamp()
            }

            self.cache_path.write_text(json.dumps(cache_data, indent=4))

        except IOError as e:
            # 写入失败不应中断主流程，只打印警告
            print(f"Warning: 无法写入 token 缓存文件. 错误: {e}")

    # 6. 修改：原 _fetch_access_token 重命名
    def _fetch_access_token_from_api(self) -> str:
        """
        私有辅助方法：从服务器获取新 token 并更新所有缓存。
        """
        params = {"corpid": self.corpid, "corpsecret": self.corpsecret}

        try:
            response = self.session.get(self.TOKEN_URL, params=params)
            js = self._handle_api_response(response)
        except Exception as e:
            raise WechatEnterpriseError(f"获取 token 失败: {e}", -1)

        access_token = js["access_token"]
        # API 返回的有效期，单位秒 (默认为 7200)
        expires_in = js.get("expires_in", 7200)

        now = datetime.now()
        # 真实的过期时间（用于文件缓存）
        real_expires_at_dt = now + timedelta(seconds=expires_in)
        # 带缓冲区的过期时间（用于内存缓存）
        buffered_expires_at_dt = now + timedelta(seconds=expires_in - self.TOKEN_EXPIRATION_BUFFER)

        # 1. 更新内存缓存
        self._access_token = access_token
        self._token_expires_at = buffered_expires_at_dt

        # 2. 更新文件缓存 (如果启用)
        self._save_token_to_file(access_token, real_expires_at_dt)

        return access_token

    # 7. 修改：get_access_token 实现混合缓存逻辑
    def get_access_token(self) -> str:
        """
        获取企业微信应用 token (带内存缓存和文件缓存)。

        缓存策略:
        1. 检查内存缓存 (最快)
        2. 检查文件缓存 (次快)
        3. 从 API 获取 (最慢)
        """
        # 1. 检查内存缓存
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        # 2. 检查文件缓存 (如果启用)
        token = self._load_token_from_file()
        if token:
            return token # _load_token_from_file 已更新内存缓存

        # 3. 缓存均无效，从 API 获取
        return self._fetch_access_token_from_api()


    def get_department_id(self, dept_id: int = 0) -> Dict[str, Any]:
        """获取部门列表"""
        return self._api_get(self.DEPT_SIMPLELIST_URL, params={"id": dept_id})

    def get_department_userlist(self, department_id: int = 1) -> Dict[str, Any]:
        """获取部门成员简易列表"""
        return self._api_get(self.USER_SIMPLELIST_URL, params={"department_id": department_id})

    def get_user_info(self, userid: str) -> Dict[str, Any]:
        """获取成员信息"""
        return self._api_get(self.GET_USER_URL, params={"userid": userid})

    def get_userid(self, telephone: str) -> Optional[str]:
        """根据手机号获取成员 userid"""
        response_json = self._api_post(self.GET_USERID_URL, json_data={"mobile": telephone})
        return response_json.get("userid")

    def upload_file(self, filepath: str, filename: str, file_type: str = "file") -> str:
        """上传文件"""
        params = {"type": file_type}
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                response_json = self._api_post(self.UPLOAD_URL, params=params, files=files)
            return response_json["media_id"]
        except FileNotFoundError:
            raise WechatEnterpriseError(f"文件未找到: {filepath}", -1)
        except Exception as e:
            raise WechatEnterpriseError(f"文件上传失败: {e}", -1)

    def _send(self, msg_type: str, users: List[str],
              content: Optional[str] = None,
              media_id: Optional[str] = None) -> Dict[str, Any]:
        """发送消息的私有核心方法"""
        userid_str = "|".join(users)
        data: Dict[str, Any] = {
            "touser": userid_str, "msgtype": msg_type, "agentid": self.appid,
            "safe": 0, "enable_id_trans": 1, "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800,
        }

        if msg_type == "text":
            if content is None: raise ValueError("文本消息 'content' 不能为空")
            data[msg_type] = {"content": content}
        elif msg_type == "markdown":
            if content is None: raise ValueError("Markdown 消息 'content' 不能为空")
            data[msg_type] = {"content": content}
        elif msg_type in ("image", "file", "voice", "video"):
            if media_id is None: raise ValueError(f"{msg_type} 消息 'media_id' 不能为空")
            data[msg_type] = {"media_id": media_id}
        else:
            raise ValueError(f"不支持的消息类型: {msg_type}")
        return self._api_post(self.SEND_URL, json_data=data)

    def send_image(self, image_path: str, users: List[str]) -> Dict[str, Any]:
        """发送图片给多个用户"""
        media_id = self.upload_file(image_path, Path(image_path).name, file_type="image")
        return self._send(msg_type="image", users=users, media_id=media_id)

    def send_file(self, file_path: str, users: List[str]) -> Dict[str, Any]:
        """发送文件给多个用户"""
        media_id = self.upload_file(file_path, Path(file_path).name, file_type="file")
        return self._send(msg_type="file", users=users, media_id=media_id)

    def send_text(self, content: str, users: List[str]) -> Dict[str, Any]:
        """发送文本消息给多个用户"""
        return self._send(msg_type="text", users=users, content=content)

    def send_markdown(self, content: str, users: List[str]) -> Dict[str, Any]:
        """发送 Markdown 消息给多个用户"""
        return self._send(msg_type="markdown", users=users, content=content)

