from rest_framework.serializers import ModelSerializer

from apps.user.models import User


class AdminSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        # 或修改原有的选项参数 密码为只读
        extra_kwargs = {
            'password': {'write_only': True}
        }

        # 重写 create 方法： 用于添加管理员权限
        def create(self, validated_data):
            # 1. 调用父类create方法
            admin = super().create(validated_data)
            # 2. 对用户密码进行加密
            password = validated_data['password']
            # 3. 调用set_password
            admin.set_password(password)
            # 4. 设置为管理员
            admin.is_staff = True
            # 5. 保存管理员数据
            admin.save()
            # 6. 返回数据
            return admin

        # 重写 update 方法： 用于更改管理员权限
        def update(self, instance, validated_data):
            # 1. 调用父类update方法实现数据更新
            super().update(instance, validated_data)
            # 2. 获取用户密码
            password = validated_data.get('password')
            # 3. 判断是否用户修改了密码
            if not password:
                instance.set_password(password)
                instance.save()

            # 4. 返回实例数据
            return instance
