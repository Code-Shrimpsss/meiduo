from datetime import date, timedelta
# from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import User


# 当日活跃用户
class UserDailyActiveCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. 获取日期
        now_date = date.today()
        # 2. 获取用户总数
        count = User.objects.filter(last_login__gte=now_date).count()
        # 3. 返回值
        return Response({
            'count': count,
            'date': now_date
        })


# 当日下单用户
class UserDailyOrderCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. 获取日期
        now_date = date.today()
        # 2. 获取当日下单用户总数
        count = User.objects.filter(orderinfo__create_time__gte=now_date).count()
        # 3. 返回值
        return Response({
            "count": count,
            "date": now_date
        })


# 当日新增用户
class UserDayCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. 获取日期
        now_date = date.today()
        # 2. 获取当日下单用户总数
        count = User.objects.filter(date_joined__gte=now_date).count()
        # 3. 返回值
        return Response({
            "count": count,
            "date": now_date
        })


# 当月新增用户
class UserMonthCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. 获取日期
        now_date = date.today()
        # 2. 获取一个月前日期
        start_date = now_date - timedelta(days=30)
        # 3. 保持每天用户量的列表
        date_list = []
        print(111)
        # 4. 循环遍历
        for i in range(30):
            # 获取当天日期
            index_date = start_date + timedelta(days=i)
            # 获取下一天日期
            cur_date = start_date + timedelta(days=i + 1)
            # 查询比较
            count = User.objects.filter(date_joined__gte=index_date, date_joined__lt=cur_date).count()

            date_list.append({
                'count': count,
                'date': index_date
            })
        return Response(date_list)

