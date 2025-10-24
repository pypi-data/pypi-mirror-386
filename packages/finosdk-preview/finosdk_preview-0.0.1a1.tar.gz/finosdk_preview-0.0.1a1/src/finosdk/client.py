import json
from typing import Any, Dict, List, Optional

import requests


class APIError(Exception):
    pass


class Client:
    """
    轻量 HTTP 客户端
    base_url 期望是你的 /data_api 根，比如: http://127.0.0.1:8003/data_api
    SDK 会自动补全 /factor/xxx 路径
    """
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8003/data_api",
        token: Optional[str] = None,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._headers = {"Content-Type": "application/json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    # ---------- 基础 POST ----------
    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Any:
        """
        endpoint:
          - 简写: "fac_carry" => /factor/fac_carry
          - 或完整: "factor/fac_carry" / "factor/csft_bkt_perf"
        """
        if "/" not in endpoint:
            path = f"/factor/{endpoint}"
        else:
            path = f"/{endpoint.lstrip('/')}"
        url = f"{self.base_url}{path}"

        r = self._session.post(
            url,
            data=json.dumps(payload),
            headers=self._headers,
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise APIError(f"HTTP {r.status_code}: {r.text}")
        try:
            ret = r.json()
        except Exception as e:
            raise APIError(f"Invalid JSON response: {e}\nText: {r.text}") from e

        code = ret.get("code", 500)
        if code != 200:
            raise APIError(ret.get("msg") or ret.get("message") or "API error")

        # 兼容服务端返回 data / obj 两种字段
        data = ret.get("data", None)
        if data is None:
            data = ret.get("obj", None)
        return data

    # ---------- fac_* 通用 ----------
    def _fac_generic(
        self,
        endpoint: str,
        *,
        start_date: str,
        end_date: str,
        code_list: Optional[List[str]] = None,
        factor: Optional[List[str]] = None,
        section: Optional[List[str]] = None,
    ):
        payload: Dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if code_list:
            payload["code_list"] = code_list
        if factor:
            payload["factor"] = factor
        if section:
            payload["section"] = section
        return self._post(endpoint, payload)

    def fac_carry(self, **kwargs):      return self._fac_generic("fac_carry",      **kwargs)
    def fac_trend(self, **kwargs):       return self._fac_generic("fac_trend",     **kwargs)
    def fac_position(self, **kwargs):     return self._fac_generic("fac_position",     **kwargs)
    def fac_futurespot(self, **kwargs): return self._fac_generic("fac_futurespot", **kwargs)
    def fac_value(self, **kwargs):      return self._fac_generic("fac_value",      **kwargs)
    def fac_warrant(self, **kwargs):    return self._fac_generic("fac_warrant",    **kwargs)
    def fac_volatility(self, **kwargs): return self._fac_generic("fac_volatility", **kwargs)

    # ---------- csft_* 通用 ----------
    def _csft_generic(
        self,
        endpoint: str,
        *,
        start_date: str,
        end_date: str,
        factor: Optional[List[str]] = None,
    ):
        payload: Dict[str, Any] = {"start_date": start_date, "end_date": end_date}
        # factor 不传或传 [] => 全量
        if factor:
            payload["factor"] = factor
        return self._post(endpoint, payload)

    def csft_bkt_perf(self, **kwargs):  return self._csft_generic("csft_bkt_perf",  **kwargs)
    def csft_bkt_data(self, **kwargs):  return self._csft_generic("csft_bkt_data",  **kwargs)
    def csft_bkt_dcp(self,  **kwargs):  return self._csft_generic("csft_bkt_dcp",   **kwargs)
    def csft_test_perf(self, **kwargs): return self._csft_generic("csft_test_perf", **kwargs)
    def csft_test_data(self, **kwargs): return self._csft_generic("csft_test_data", **kwargs)
    def csft_test_dcp(self,  **kwargs): return self._csft_generic("csft_test_dcp",  **kwargs)
