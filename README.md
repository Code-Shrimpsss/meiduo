# 美多后台使用文档 #

### 使用 ###

项目 `gitee` 路径：https://gitee.com/jiao-yan-xia/meiduo-backstage/tree/master/

1) 使用 `git clone` 将项目拷贝
2) 在项目根目录使用 `npm install` 安装依赖

------

以下是项目开发流程：

### 跨域问题 ###

在美多商场项目的 `setting.py` 中使用`CORS`来解决后端对跨域访问的支持

1. 安装

   ```
   pip install django-cors-headers
   ```

2. 添加应用

   ```python
   INSTALLED_APPS = (
       ...
       'corsheaders',
       ...
   )
   ```

3. 中间层设置

   ```python
   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       ...
   ]
   ```

4. 添加白名单

   ```python
   # CORS
   CORS_ORIGIN_WHITELIST = (
       'http://127.0.0.1:8080',
       'http://localhost:8090',
       'http://www.meiduo.site:8080',
       'http://www.meiduo.site:8090'
   )
   CORS_ALLOW_CREDENTIALS = True  # 允许携带cookie
   ```

凡是出现在白名单中的域名，都可以访问后端接口

> `CORS_ALLOW_CREDENTIALS` 表示为 在跨域访问中后端是否支持对`cookie`的操作

### 使用 Django REST framework JWT ###

1. 安装

   ```python
   pip install djangorestframework-jwt
   ```

2. 配置

   ```python
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': (
           'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
           'rest_framework.authentication.SessionAuthentication',
           'rest_framework.authentication.BasicAuthentication',
       ),
   }
   import datetime
   JWT_AUTH = {
       'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),
   }
   ```

   `JWT_EXPIRATION_DELTA` 指明 `token`的有效期

## 账号登录 ##

### 1. 业务说明 ###

验证用户名和密码，验证成功后，为用户签发JWT，前端将签发的JWT保存下来。

### 2. 后端接口设计 ###

**请求方式**： **POST** `meiduo_admin/authorizations/`

**请求参数**： JSON 或 表单

| 参数名   | 类型 | 是否必须 | 说明   |
| :------- | :--- | :------- | :----- |
| username | str  | 是       | 用户名 |
| password | str  | 是       | 密码   |

**返回数据**： `JSON`

```
{
    "username": "python",
    "user_id": 1,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo5LCJ1c2VybmFtZSI6InB5dGhvbjgiLCJleHAiOjE1MjgxODI2MzQsImVtYWlsIjoiIn0.ejjVvEWxrBvbp18QIjQbL1TFE0c0ejQgizui_AROlAU"
}
```

| 返回值   | 类型 | 是否必须 | 说明         |
| :------- | :--- | :------- | :----------- |
| username | str  | 是       | 用户名       |
| id       | int  | 是       | 用户id       |
| token    | str  | 是       | 身份认证凭据 |

### 3. 后端实现 ###

**Django REST framework JWT 提供了登录 JWT的 视图，可以直接使用**

```python
from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    path('authorizations/', obtain_jwt_token),
]
```

但是默认的返回值仅有`token`，我们还需在返回值中增加`username`和 `user_id`。

通过修改该视图的返回值可以完成我们的需求，在 `meiduo_amin/utils.py` 中，创建：

```python
def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        'token': token,
        'id': user.id,
        'username': user.username
    }
```

### 4. 修改配置文件 ###

在项目 `setting.py` 中修改配置文件

```python
# JWT配置
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'apps.meiduo_admin.utils.jwt_response_payload_handler',
}
```



## 自定义视图和序列化器 ##

**问题：**我们发现序列化器的验证 **只是判断一下是否激活**，所有任何用户都可以登录 

**解决：**为了防止任何用户都可以登录 ，这里用自定义方式重写 `JSONWebTokenSerializer` 中的 `validate` 类：



1. 新建`login.py`文件进行重写

   1) 

   ```python
   from rest_framework_jwt.views import JSONWebTokenAPIView
   from rest_framework_jwt.serializers import JSONWebTokenSerializer
   from django.contrib.auth import authenticate
   from rest_framework import serializers
   from django.utils.translation import ugettext as _
   from rest_framework_jwt.settings import api_settings
   jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
   jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
   
   class AdminJSONWebTokenSerializer(JSONWebTokenSerializer):
   
       def validate(self, attrs):
           credentials = {
               self.username_field: attrs.get(self.username_field),
               'password': attrs.get('password')
           }
   
           if all(credentials.values()):
               user = authenticate(**credentials)
   
               if user:
                   if not user.is_active:
                       msg = _('User account is disabled.')
                       raise serializers.ValidationError(msg)
                   # 新增添加
                   if not user.is_staff:
                       msg = _('User account is disabled.')
                       raise serializers.ValidationError(msg)
   
                   payload = jwt_payload_handler(user)
   
                   return {
                       'token': jwt_encode_handler(payload),
                       'user': user
                   }
               else:
                   msg = _('Unable to log in with provided credentials.')
                   raise serializers.ValidationError(msg)
           else:
               msg = _('Must include "{username_field}" and "password".')
               msg = msg.format(username_field=self.username_field)
               raise serializers.ValidationError(msg)
   
   class AdminJsonWebTokenAPIView(JSONWebTokenAPIView):
   
       serializer_class = AdminJSONWebTokenSerializer
   
   admin_jwt_token=AdminJsonWebTokenAPIView.as_view()
   ```

   

2. 路由修改为

   ```python
   from .views.login import admin_jwt_token
   urlpatterns = [
       # 登录    
       path(r'authorizations/',admin_jwt_token),
   ]
   ```

## 日活跃用户统计 ##

### 接口分析 ###

**请求方式**：GET`/meiduo_admin/statistical/day_active/`

**请求参数**： 通过请求头传递jwt token数据。

**返回数据**： JSON

```python
{
        "count": "活跃用户量",
        "date": "日期"
}
```

| 返回值 | 类型 | 是否必须 | 说明       |
| :----- | :--- | :------- | :--------- |
| count  | int  | 是       | 活跃用户量 |
| date   | date | 是       | 日期       |

### 后端实现 ###

**count_views.py 视图：**

```python
class UserDailyActiveCountView(APIView):

    permission_classes = [IsAdminUser]

    def get(self,request):
        # 获取当前日期
        now_date = date.today()
        # 获取活跃用户总数
        count = User.objects.filter(last_login__gte=now_date).count()
        return Response({
            'count': count,
            'date': now_date
        })
```

**urls.py 路由：**

```python
from .view.count_views import UserDailyActiveCountView
    
urlpatterns = [
    # 用于返回 当日活跃人数
    path('statistical/day_active/', UserDailyActiveCountView.as_view()),
    # 用于返回 当日下单人数
    path('statistical/day_orders/', UserDailyOrderCountView.as_view()),
    # 用于返回 当日新增人数
    path('statistical/day_increment/', UserDayCountView.as_view()),
    # 用于返回 当月新增人数
    path('statistical/month_increment/', UserMonthCountView.as_view()),
    # 用于返回 用户总人数
    path('users/', UserListView.as_view()),

]

```



## 日下单用户量统计 ##

### 接口分析 ###

**请求方式**：GET`/meiduo_admin/statistical/day_orders/`

**请求参数**： 通过请求头传递jwt token数据。

**返回数据**： JSON

```python
{
        "count": "下单用户量",
        "date": "日期"
}
```

| 返回值 | 类型 | 是否必须 | 说明       |
| :----- | :--- | :------- | :--------- |
| count  | int  | 是       | 下单用户量 |
| date   | date | 是       | 日期       |

### 后端实现 ###

**count_views.py 视图：**

```python
class UserDailyOrderCountView(APIView):

    permission_classes = [IsAdminUser]

    def get(self,request):
        # 获取当前日期
        now_date = date.today()
        # 获取当日下单用户数量  orders__create_time 订单创建时间
        count = User.objects.filter(orderinfo__create_time__gte=now_date).count()
        return Response({
            "count": count,
            "date": now_date
        })
```

**urls.py 路由：**

```python
from .view.count_views import UserDailyOrderCountView
    
urlpatterns = [
    # 用于返回 当日下单人数
    path('statistical/day_orders/', UserDailyOrderCountView.as_view()),
]

```



## 日增用户统计 ##

### 接口分析 ###

**请求方式**：GET`/meiduo_admin/statistical/day_increment/`

**请求参数**： 通过请求头传递 jwt token数据。

**返回数据**： JSON

```python
{
        "count": "下单用户量",
        "date": "日期"
}
```

| 返回值 | 类型 | 是否必须 | 说明       |
| :----- | :--- | :------- | :--------- |
| count  | int  | 是       | 下单用户量 |
| date   | date | 是       | 日期       |

### 后端实现 ###

**count_views.py 视图：**

```python
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
```

**urls.py 路由：**

```python
 from .view.count_views import UserDayCountView
     
 urlpatterns = [
     # 用于返回 当日新增人数
     path('statistical/day_increment/', UserDayCountView.as_view()),
 ]
 
```

## 月增用户统计 ##

### 接口分析 ###

**请求方式**：GET`/meiduo_admin/statistical/month_increment/`

**请求参数**： 通过请求头传递jwt token数据。

**返回数据**： JSON

```python
 [ {
            "count": "用户量",
            "date": "日期"
        },
        {
            "count": "用户量",
            "date": "日期"
        },
        ...
]
```

| 返回值 | 类型 | 是否必须 | 说明       |
| :----- | :--- | :------- | :--------- |
| count  | int  | 是       | 下单用户量 |
| date   | date | 是       | 日期       |

### 后端实现 ###

**count_views.py 视图：**

```python
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
```

**urls.py 路由：**

```python
 from .view.count_views import  UserMonthCountView
     
 urlpatterns = [
     # 用于返回 当月新增人数
     path('statistical/month_increment/', UserMonthCountView.as_view()),
 
 ]
 
```

## 用户显示与查询 ##

### 接口分析 ###

**请求方式**：GET`/meiduo_admin/users/?keyword=<搜索内容>&page=<页码>&pagesize=<页容量>`

**请求参数**： 通过请求头传递 jwt token 数据

| 参数     | 类型 | 是否必须 | 说明       |
| :------- | :--- | :------- | :--------- |
| keyword  | str  | 否       | 搜索用户名 |
| page     | int  | 否       | 页码       |
| pagesize | int  | 否       | 页容量     |

**返回数据**： JSON

```python
 {
        "count": "用户总量",
        "lists": [
            {
                "id": "用户id",
                "username": "用户名",
                "mobile": "手机号",
                "email": "邮箱"
            },
            ...
        ],
        "page": "页码",
        "pages": "总页数",
        "pagesize": "页容量"
      }
```

| 返回值   | 类型 | 是否必须 | 说明     |
| :------- | :--- | :------- | :------- |
| count    | int  | 是       | 用户总量 |
| Lists    | 数组 | 是       | 用户信息 |
| page     | int  | 是       | 页码     |
| pages    | int  | 是       | 总页数   |
| pagesize | int  | 是       | 页容量   |

### 用户显示查询使用 ###

1. 创建用户查询视图 `user_views.py`

   ```python
   from rest_framework.generics import ListAPIView
   from apps.meiduo_admin.serializers.user_serializers import UserModelSerializer
   from apps.meiduo_admin.utils import PageNum
   from apps.user.models import User
   
   
   class UserListView(ListAPIView):
       # 1. 指定查询集 (预加载)
       # queryset = User.objects.all()
       # 2. 指定序列化器
       serializer_class = UserModelSerializer
       # 3. 分页类
       pagination_class = PageNum
       
        # 重写 get_querysey
       def get_queryset(self):
           # 1. 获取前端传递的 keyword
           keyword = self.request.query_params.get('keyword')
           # 2. 判断 (若不存在或为空 则返回全部, 否则返回查询对应的keyword)
           if not keyword:
               return User.objects.all()
           else:
               return User.objects.filter(username=keyword)
   
   ```

   

2. 自定义用户序列化器

   ```python
   from rest_framework.serializers import ModelSerializer
   from apps.user.models import User
   
   
   class UserModelSerializer(ModelSerializer):
       class Meta:
           model = User
           fields = ('id', 'username', 'mobile', 'email'，'password')
   
   ```

   

3. 在 `utils.py` 文件中 创建分类页，重写 `get_paginated_response` 方法

   ```python
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
   
   ```

   

4. 定义路由

   ```python
   # 用于返回 用户总人数
   path('users/', UserListView.as_view()),
   ```

   

   

## 上述总路由 ##



![](https://s3.bmp.ovh/imgs/2022/03/9ab3dc2ad5d58f9a.png)

## 用户新增功能 ##

### 接口分析 ###

**请求方式**：POST `/meiduo_admin/users/`

**请求参数**： 通过请求头传递 jwt token数据。

| 参数     | 类型 | 是否必须 | 说明   |
| :------- | :--- | :------- | :----- |
| username | str  | 是       | 用户名 |
| mobile   | str  | 是       | 手机号 |
| password | int  | 是       | 密码   |
| email    | str  | 否       | 邮箱   |

**返回数据**： JSON

```js
{
        "id": "用户id",
        "username": "用户名",
        "mobile": "手机号",
        "email": "邮箱"
}
```

| 返回值   | 类型 | 是否必须 | 说明   |
| :------- | :--- | :------- | :----- |
| id       | int  | 是       | 用户id |
| username | str  | 是       | 用户名 |
| mobile   | str  | 是       | 手机号 |
| email    | str  | 是       | 邮箱   |

### 用户新增使用 ###

1. 在 `UserView` 类视图中对原有的类视图进行改写为 **继承ListCreateAPIView**

   ```python
   from rest_framework.generics import ListCreateAPIView
   class UserListView(ListCreateAPIView):
        ....
   ```

   

2. 在 `user_serializer.py` 文件的 `UserModelSerializer` 中 重写 `create`方法 

   ```python
   class UserModelSerializer(ModelSerializer):
       class Meta:
           model = User
           # 添加字段传递
           fields = ('id', 'username', 'mobile', 'email', 'password')
   
           # < 重写 Create 方法 >
           def create(self, validated_data):
               # 对于用户数据进行保存与密码加密
               user = User.objects.create(**validated_data)
               return user
   ```

   

## SKU数据获取 ##

### 接口分析 ###

**请求方式**： GET`/meiduo_admin/skus/simple/`

**请求参数**： 通过请求头传递 jwt token数据。

**返回数据**： JSON

```python
 [
        {
            "id": 1,
            "name": "Apple MacBook Pro 13.3英寸笔记本 银色"
        },
        {
            "id": 2,
            "name": "Apple MacBook Pro 13.3英寸笔记本 深灰色"
        },
        ......
    ]
```

| 返回值 | 类型 | 是否必须 | 说明        |
| :----- | :--- | :------- | :---------- |
| Id     | int  | 是       | sku商品id   |
| name   | 数组 | 是       | Sku商品名称 |

### SKU数据获取使用 ###

**image_views.py 视图：**

```python
# 用于返回 所有SKU
class SKUView(APIView):
    def get(self, request):
        data = SKU.objects.all()
        ser = SKUSerializer(data, many=True)
        return Response(ser.data)
```

**user_serializer.py 序列化器**

```python
# 获取所有SKU的序列号器
class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ('id', 'name')
```

**urls.py 路由：**

```python
# 用于返回 所有SKU
path('skus/simple/', SKUView.as_view()),
```

## 图片获取 ##

### 接口分析 ###

**请求方式**： GET`/meiduo_admin/skus/images/`

**请求参数**： 通过请求头传递jwt token数据。

**返回数据**： JSON

```js
{
        "count": "图片总数量",
        "lists": [
              {
                "id": "图片id",
                "sku": "SKU商品id",
                "image": "图片地址"
              }
            ...
       ],
       "page": "页码",
       "pages": "总页数",
       "pagesize": "页容量"
  }
```

| 返回值   | 类型 | 是否必须 | 说明     |
| :------- | :--- | :------- | :------- |
| count    | int  | 是       | 图片总量 |
| lists    | 数组 | 是       | 图片信息 |
| page     | int  | 是       | 页码     |
| pages    | int  | 是       | 总页数   |
| pagesize | int  | 是       | 页容量   |

### 图片获取使用 ###

**image_views.py 视图：**

```python
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
```

**urls.py 路由：**

`所有图片路由通用路由`

```python
urlpatterns = []

# ----- 使用默认实例
router = DefaultRouter()
# ----- 注册路由
router.register(r'skus/images', ImageView, basename='imagesku')
# ----- 追加到 urlpatterns 中
urlpatterns += router.urls
```

## 图片保存 ##

### 接口分析 ###

**请求方式**：POST`/meiduo_admin/skus/images/`

**请求参数**： 通过请求头传递jwt token数据。

```
表单提交数据:
        "sku": "SKU商品id",
        "image": "SKU商品图片"
```

| 参数  | 类型 | 是否必须 | 说明        |
| :---- | :--- | :------- | :---------- |
| sku   | str  | 是       | SKU商品id   |
| image | Fiel | 是       | SKU商品图片 |

**返回数据**： JSON

```js
{
        "id": "图片id",
        "sku": "SKU商品id",
        "image": "图片地址"
    }
```

| 参数  | 类型 | 是否必须 | 说明      |
| :---- | :--- | :------- | :-------- |
| id    | Int  | 是       | 图片id    |
| sku   | int  | 是       | SKU商品id |
| image | str  | 是       | 图片地址  |

### 图片保存使用 ###

> 图片保存更新与删除用的是同一个视图

```python
class ImageView(ModelViewSet):
    # 1. 指定查询集
    queryset = SKUImage.objects.all()
    # 2. 指定序列化器
    serializer_class = ImageSerializer
    # 3. 分页类
    pagination_class = PageNum

    # 重写Create类的保存业务逻辑
    def create(self, request, *args, **kwargs):
        # 1. 接收参数
        sku_id = request.data.get('sku')
        print(request.data)
        print(sku_id)
        image = request.FILES.get('image')
        print(image)

        # 2. 把图片上传到 fastdfs 中
        from fdfs_client.client import Fdfs_client
        # 2.1 保存图片对应路径
        client = Fdfs_client('utils/fastdfs/client.conf')
        result = client.upload_by_buffer(image.read())
        print(result)
        # 2.2 判断状态码
        if result.get("Status") != 'Upload successed.':
            return Response(status=status.HTTP_400_BAD_REQUEST)
            # 2.3 将fastdfs中取出的地址存放到数据库
        file_id = result.get("Remote file_id")
        print('file_id', file_id)

        # 3. 把图片的地址和sku_id使用的模型类SKUImage保存到数据库
        SKUImage.objects.create(sku_id=sku_id, image=file_id)

        # 4. 返回响应
        return Response(status=status.HTTP_201_CREATED)
```



## 图片更新 ##

### 接口分析 ###

**请求方式**： PUT`/meiduo_admin/skus/images/(?P<pk>\d+)/`

**请求参数**： 通过请求头传递jwt token数据。

```python
表单提交数据:
        "sku": "SKU商品id",
        "image": "SKU商品图片"
```

| 参数  | 类型 | 是否必须 | 说明        |
| :---- | :--- | :------- | :---------- |
| sku   | str  | 是       | SKU商品id   |
| image | Fiel | 是       | SKU商品图片 |

**返回数据**： JSON

```python
  {
        "id": "图片id",
        "sku": "SKU商品id",
        "image": "图片地址"
    }
```

| 参数  | 类型 | 是否必须 | 说明      |
| :---- | :--- | :------- | :-------- |
| id    | Int  | 是       | 图片id    |
| sku   | int  | 是       | SKU商品id |
| image | str  | 是       | 图片地址  |

### 图片更新使用 ###

```python
class ImageView(ModelViewSet):
    # 1. 指定查询集
    queryset = SKUImage.objects.all()
    # 2. 指定序列化器
    serializer_class = ImageSerializer
    # 3. 分页类
    pagination_class = PageNum


# 重写update类的更新业务逻辑
    def update(self, request, *args, **kwargs):
        # 1. 接收参数
        image = request.FILES.get('image')
        # 1.1 获取修改的模型类对象的id
        pk = kwargs.get('pk')
        print("kwargs", kwargs)

        # 2. 把图片上传到 fastdfs 中
        from fdfs_client.client import Fdfs_client
        # 2.1 保存图片对应路径
        client = Fdfs_client('utils/fastdfs/client.conf')
        result = client.upload_by_buffer(image.read())
        # 2.2 判断状态码
        if result.get('Status') != 'Upload successed.':
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 2.3 将fastdfs中取出的地址存放到数据库
        file_id = result.get("Remote file_id")
        print('file_id', file_id)

        # 3. 获取要修改的对象将新的地址保存
        sku_image = SKUImage.objects.get(id=pk)
        sku_image.image = file_id
        sku_image.save()

        # 4. 返回响应
        return Response(status=status.HTTP_201_CREATED)
```



## 图片删除 ##

### 接口分析 ###

**请求方式**： Delte`/meiduo_admin/skus/images/(?P<pk>\d+)/`

**请求参数**： 通过请求头传递jwt token数据。

**返回数据**： JSON

返回空

### 逻辑删除 ###

1) 在 **SKUImage**模型字段中添加 `is_delete` 字段

   ![](https://s3.bmp.ovh/imgs/2022/03/e6790aed88e5f3ac.png)

2) 在 **image_serializer** 序列化器中添加  `is_delete` 字段

   ![](https://s3.bmp.ovh/imgs/2022/03/ba4ffd776b3c744a.png)

3) 在 **image.views.py** 视图中重写 `destroy`方法

   ![](https://s3.bmp.ovh/imgs/2022/03/83108fb94dfb92d3.png)

   

   **这里要特别注意将查询集更改为 `is_delete`为 0 或 False** 

### 真实删除 ###

```python
class ImageView(ModelViewSet):
    # 1. 指定查询集
    queryset = SKUImage.objects.all()
    # 2. 指定序列化器
    serializer_class = ImageSerializer
    # 3. 分页类
    pagination_class = PageNum

# 重写destroy类的删除业务逻辑
    # ---- 真实删除
    def destroy(self, request, *args, **kwargs):
        # 1. 接收参数
        # 1.1 获取要删除的对象ID
        pk = kwargs.get('pk')
        # 1.2 获取要删除的对象
        img = SKUImage.objects.get(id=pk)
        # 1.3 获取要删除的对象url
        imglongurl = img.image.url
        # 1.4 获取要截取后的url
        imgurl = imglongurl[28:]

        # 2. 把图片上传到 fastdfs 中
        from fdfs_client.client import Fdfs_client
        # 2.1 获取图片地址
        client = Fdfs_client('utils/fastdfs/client.conf')
        # 2.2 真实删除图片
        client.delete_file(imgurl)
        # 2.3 真实删除数据
        img.delete()

        # 3. 返回数据
        return Response(status=status.HTTP_201_CREATED)
```


