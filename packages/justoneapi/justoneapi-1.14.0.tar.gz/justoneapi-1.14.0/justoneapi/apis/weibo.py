from justoneapi.apis import request_util
from justoneapi.log import logger


class WeiboAPI:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

    def search_all_v2(self, q: str, start_day: str, start_hour: int, end_day: str, end_hour: int, page: int):
        url = f"{self.base_url}/api/weibo/search-all/v2"
        params = {
            "token": self.token,
            "q": q,
            "startDay": start_day,
            "startHour": start_hour,
            "endDay": end_day,
            "endHour": end_hour,
            "page": page,
        }

        has_next_page = False
        result, data, message = request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("has_next_page", False) is True:
                    has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def search_all_v3(self, q: str, page: int):
        url = f"{self.base_url}/api/weibo/search-all/v3"
        params = {
            "token": self.token,
            "q": q,
            "page": page,
        }

        has_next_page = False
        result, data, message = request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("cards"):
                    has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def get_weibo_detail_v1(self, id: str):
        url = f"{self.base_url}/api/weibo/get-weibo-detail/v1"
        params = {
            "token": self.token,
            "id": id,
        }
        return request_util.get_request(url, params)

    def get_user_detail_v1(self, uid: str):
        url = f"{self.base_url}/api/weibo/get-user-detail/v1"
        params = {
            "token": self.token,
            "uid": uid,
        }
        return request_util.get_request(url, params)

    def get_fans_v1(self, uid: str, page: int):
        url = f"{self.base_url}/api/weibo/get-fans/v1"
        params = {
            "token": self.token,
            "uid": uid,
            "page": page,
        }
        return request_util.get_request(url, params)

    def get_followers_v1(self, uid: str, page: int):
        url = f"{self.base_url}/api/weibo/get-followers/v1"
        params = {
            "token": self.token,
            "uid": uid,
            "page": page,
        }
        return request_util.get_request(url, params)

    def get_user_post_v1(self, uid: str, page: int, since_id: str = None):
        url = f"{self.base_url}/api/weibo/get-user-post/v1"
        params = {
            "token": self.token,
            "uid": uid,
            "page": page,
        }
        if since_id:
            params["sinceId"] = since_id

        return request_util.get_request(url, params)

