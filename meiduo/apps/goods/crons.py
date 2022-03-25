import os

from django.template import loader

from apps.ad.models import ContentCategory
from meiduo import settings
from utils.goodsuitls import get_categories


def generate_static_index_html():
    try:
        categories = get_categories()
    except Exception as e:
        print(e)
        return {'code': 1, 'errmsg': 'get data error'}

        # 广告数据
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # 渲染模板的上下文
    context = {
        'categories': categories,
        'contents': contents,
    }


    # 获取模板对象
    template = loader.get_template("index.html")
    html_text = template.render(context)
    # 渲染好的模板保存到file
    file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'front_end_pc/index.html')
    with open(file_path, 'w') as f:
        f.write(html_text)


