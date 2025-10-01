from django import template
# 模板過濾器

register = template.Library()

@register.filter
def split(value, arg):
    """將字符串按指定分隔符分割"""
    return value.split(arg)

@register.filter
def strip(value):
    """移除字符串兩端的空白"""
    return value.strip() 