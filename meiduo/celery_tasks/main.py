# celery启动文件
from celery import Celery

# 为celery使用django配置文件进行设置
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo.settings')

# 创建celery实例
celery_app = Celery('celery_tasks')
# 2.加载celery实例
celery_app.config_from_object('celery_tasks.config')
# 3.自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])
