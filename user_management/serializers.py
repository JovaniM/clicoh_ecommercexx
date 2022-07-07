from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user_model = get_user_model()
        password = validated_data.pop('password')
        user = user_model.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
