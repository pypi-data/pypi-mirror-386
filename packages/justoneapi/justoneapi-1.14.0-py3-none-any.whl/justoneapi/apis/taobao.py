from justoneapi.apis import request_util
from justoneapi.log import logger


class TaobaoAPI:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

    def get_item_detail_v1(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v1"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_detail_v2(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v2"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_detail_v3(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v3"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_detail_v4(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v4"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_detail_v5(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v5"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_detail_v7(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v7"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_detail_v8(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v8"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_detail_v9(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-detail/v9"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def get_item_comment_v6(self, item_id: str, page: int, order_type: str = None):
        url = f"{self.base_url}/api/taobao/get-item-comment/v6"
        params = {
            "token": self.token,
            "itemId": item_id,
            "page": page,
        }
        if order_type:
            params["orderType"] = order_type

        has_next_page = False
        result, data, message =  request_util.get_request_page(url, params)
        try:
            if data:
                if page < data.get("paginator", {}).get("lastPage", -1):
                    has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def get_item_comment_v7(self, item_id: str, page: int, order_type: str = None):
        url = f"{self.base_url}/api/taobao/get-item-comment/v7"
        params = {
            "token": self.token,
            "itemId": item_id,
            "page": page,
        }
        if order_type:
            params["orderType"] = order_type

        has_next_page = False
        result, data, message =  request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("hasNext", "false") == "true":
                    has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def get_social_feed_v1(self, item_id: str, page: int):
        url = f"{self.base_url}/api/taobao/get-social-feed/v1"
        params = {
            "token": self.token,
            "itemId": item_id,
            "page": page,
        }

        has_next_page = False
        result, data, message =  request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("pagination", {}).get("hasMore", "false") == "true":
                    has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def get_shop_item_list_v1(self, user_id: str, shop_id: str, page: int, sort: str = None):
        url = f"{self.base_url}/api/taobao/get-shop-item-list/v1"
        params = {
            "token": self.token,
            "userId": user_id,
            "shopId": shop_id,
            "page": page,
        }
        if sort:
            params["sort"] = sort

        has_next_page = False
        result, data, message =  request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("pageInitialProps", {}).get("httpData", {}).get("itemListModuleResponse", {}).get("page", {}).get("totalPages", 0) > page:
                    has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def get_shop_item_list_v9(self, user_id: str, shop_id: str, sort: str, page: int):
        url = f"{self.base_url}/api/taobao/get-shop-item-list/v9"
        params = {
            "token": self.token,
            "userId": user_id,
            "shopId": shop_id,
            "sort": sort,
            "page": page,
        }

        has_next_page = False
        result, data, message =  request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("itemsArray"):
                    if page < int(data.get("totalPage", '0')):
                        has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def get_item_sale_v5(self, item_id: str):
        url = f"{self.base_url}/api/taobao/get-item-sale/v5"
        params = {
            "token": self.token,
            "itemId": item_id,
        }
        return request_util.get_request(url, params)

    def search_item_list_v1(self, keyword: str, sort: str, page: int, tmall: bool = False, start_price: str = None, end_price: str = None):
        url = f"{self.base_url}/api/taobao/search-item-list/v1"
        params = {
            "token": self.token,
            "keyword": keyword,
            "sort": sort,
            "page": page,
        }
        if tmall:
            params["tmall"] = tmall
        if start_price:
            params["startPrice"] = start_price
        if end_price:
            params["endPrice"] = end_price

        has_next_page = False
        result, data, message =  request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("model", {}).get("page", {}).get("totalPages", 0) > page:
                    has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

    def search_item_list_v6(self, keyword: str, sort: str, page: int, tab: str = None, start_price: str = None, end_price: str = None):
        url = f"{self.base_url}/api/taobao/search-item-list/v6"
        params = {
            "token": self.token,
            "keyword": keyword,
            "sort": sort,
            "page": page,
        }
        if tab:
            params["tab"] = tab
        if start_price:
            params["startPrice"] = start_price
        if end_price:
            params["endPrice"] = end_price

        has_next_page = False
        result, data, message =  request_util.get_request_page(url, params)
        try:
            if data:
                if data.get("itemsArray"):
                    if page < int(data.get("totalPage", '0')):
                        has_next_page = True
        except Exception as e:
            logger.warning(f"Pagination parse error at {url}. Contact us to fix it.")
        return result, data, message, has_next_page

