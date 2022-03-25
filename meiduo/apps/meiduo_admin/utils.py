from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


# 该方法用于返回 token
def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'username': user.username,
        'id': user.id
    }


# 该方法用于返回页数
class PageNum(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'pagesize'
    max_page_size = 10

    # 重写分页返回方法
    def get_paginated_response(self, data):
        return Response({
            'lists': data,
            'page': self.page.number,
            'pages': self.page.paginator.num_pages
        })
