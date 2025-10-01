# post/admin.py
from django.contrib import admin
from .models import Post, Comment, PostImage, PostReaction, FavoritePost

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "user", "type", "is_pinned", "is_platform_featured",
        "location_name", "dining_date", "meal_time", "created_at",
    )
    list_filter = ("type", "is_pinned", "is_platform_featured", "meal_time", "created_at")
    search_fields = (
        "id", "title", "content",
        "location_name", "location_address", "location_place_id",
        "user__username",
    )
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
    inlines = [PostImageInline]
    ordering = ("-is_platform_featured", "-is_pinned", "-created_at")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "short_content", "parent", "created_at")
    list_select_related = ("post", "user", "parent")
    search_fields = ("id", "content", "post__title", "user__username")
    autocomplete_fields = ("post", "user", "parent")
    date_hierarchy = "created_at"
    ordering = ("created_at",)

    def short_content(self, obj):
        return (obj.content[:40] + "…") if len(obj.content) > 40 else obj.content
    short_content.short_description = "內容"

@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "reaction_type", "created_at")
    list_filter = ("reaction_type", "created_at")
    search_fields = ("id", "post__title", "user__username")
    autocomplete_fields = ("post", "user")
    date_hierarchy = "created_at"

@admin.register(FavoritePost)
class FavoritePostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "created_at")
    search_fields = ("id", "user__username", "post__title")
    autocomplete_fields = ("user", "post")
    date_hierarchy = "created_at"
