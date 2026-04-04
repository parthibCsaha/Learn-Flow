from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label='Confirm Password')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'role')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs
    
    def validate_role(self, value):
        # Prevent creating admin users via API
        if value not in [User.Role.STUDENT, User.Role.INSTRUCTOR]:
            raise serializers.ValidationError('Invalid role.')
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'bio', 'profile_picture', 'date_joined')
        read_only_fields = ('id', 'email', 'role', 'date_joined')
 
 
class PublicUserSerializer(serializers.ModelSerializer):
    """Minimal public info — used in nested course serializers."""
    class Meta:
        model = User
        fields = ('id', 'username', 'profile_picture')

