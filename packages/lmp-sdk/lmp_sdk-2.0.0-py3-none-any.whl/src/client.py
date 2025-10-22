import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from .models import (
    PostAsyncInferRequest,
    PostAsyncInferResponse,
    PostAsyncInferParams,
    Message,
    TaskResponse
)
from .constants import (
    DEFAULT_API_ENDPOINT,
    DEFAULT_MODEL,
    BASE_GET_URL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_RETRIES,
)
from .exceptions import APIError, TaskTimeoutError, TaskFailedError

logger = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        token: str,
    #    task_queue: TaskQueue,
        endpoint: str = DEFAULT_API_ENDPOINT,
        worker_num: int = 100,
        timeout: int = 3600,
        use_processer: bool = True
    ):
        self.endpoint = endpoint
        self.token = token



        # 创建 Session
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=worker_num,  # 每个主机的连接池连接数
            pool_maxsize=worker_num,
            max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]),
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "content-type": "application/json",
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        })
        self.timeout = timeout

        logger.info(f"Client initialized with endpoint: {endpoint}")

    def post_async_infer(self, request: PostAsyncInferRequest) -> PostAsyncInferResponse:
        # 设置默认值
        if not request.model:
            request.model = DEFAULT_MODEL
        if request.temperature == 0:
            request.temperature = DEFAULT_TEMPERATURE
        if request.max_retries == 0:
            request.max_retries = DEFAULT_MAX_RETRIES

        if not request.contents:
            raise ValueError("No contents provided")

        # 构建参数
        params = PostAsyncInferParams(
            model=request.model,
            messages=[
                Message(role=request.role, content=request.contents)
            ],
            temperature=request.temperature,
            frequency_penalty=request.frequency_penalty,
            stream=request.stream,
            ipai_max_request_retries=request.max_retries
        )

        return self.async_infer_send(params)

    def async_infer_send(self, params: PostAsyncInferParams) -> PostAsyncInferResponse:

        try:
            response = self.session.post(
                self.endpoint,
                json=params.to_dict(),
                timeout=self.timeout
            )

            if response.status_code != 200:
                raise APIError(response.status_code, response.text)

            result = PostAsyncInferResponse.from_dict(response.json())

            return result

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(0, str(e))

    def get_task_status(self, task_id: str) -> TaskResponse:

        url = f"{BASE_GET_URL}/async_infer/{task_id}"

        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                raise APIError(response.status_code, response.text)

            return TaskResponse.from_dict(response.json())

        except requests.RequestException as e:
            logger.error(f"Get task status failed: {e}")
            raise APIError(0, str(e))

    def close(self):
        """关闭客户端"""
        self.session.close()
        logger.info("Client closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()