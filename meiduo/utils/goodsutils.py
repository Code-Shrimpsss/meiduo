from apps.goods.models import GoodsChannel


def get_categories():
    # 1 查询所有频道 先按group_id排序 group_id相等的按sequence排序
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    # 创建一个空字典 存放拼接好的总数据
    categories = {}

    for c in channels:
        # print(c)
        # 1 组装最外层数据
        # 判断group_id如果已经在字典里存在了 就不用执行了
        if c.group_id not in categories:
            categories[c.group_id] = {"channels": [], 'sub_cats': []}

        # 2 组装里面的额channels里的数据
        category = c.category  # 获取每个频道里的分类对象
        categories[c.group_id]['channels'].append({
            "id": category.id,
            "name": category.name,
            "url": c.url,
        })

        # 3  组装2级和3级分类数据
        category2 = category.subs.all()  # 获取所有的2级分类
        for c2 in category2:

            category3 = c2.subs.all()  # 获取所有的3级分类
            sub_cats3 = []  # 存放所有3级分类的数据
            for c3 in category3:
                sub_cats3.append({
                    'id': c3.id,
                    'name': c3.name
                })

            categories[c.group_id]['sub_cats'].append({
                "id": c2.id,
                'name': c2.name,
                'sub_cats': sub_cats3
            })

    return categories


def get_breadcrumb(category):
    """
    获取面包屑导航
    :param category: 商品类别
    :return: 面包屑导航字典
    """
    breadcrumb = dict(
        cat1='',
        cat2='',
        cat3=''
    )
    if category.parent is None:
        # 当前类别为一级类别
        breadcrumb['cat1'] = category.name
    elif category.subs.count() == 0:
        # 当前类别为三级
        breadcrumb['cat3'] = category.name
        breadcrumb['cat2'] = category.parent.name
        breadcrumb['cat1'] = category.parent.parent.name
    else:
        # 当前类别为二级
        breadcrumb['cat2'] = category.name
        breadcrumb['cat1'] = category.parent.name

    return breadcrumb
