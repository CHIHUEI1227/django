# restaurants/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Restaurant, RestaurantOpeningHour, RestaurantPhoto, RestaurantReview,
    RestaurantAttribute, RestaurantSourceMeta,
    RestaurantIndicatorDetail, RestaurantIndicatorSummary
)

# ========== Inlines（掛在 Restaurant 下） ==========
class OpeningHourInline(admin.TabularInline):
    model = RestaurantOpeningHour
    fields = ("weekday", "open_time", "close_time", "crosses_midnight")
    extra = 0
    show_change_link = True

class AttributeInline(admin.TabularInline):
    model = RestaurantAttribute
    fields = ("key", "value", "source")
    extra = 0
    show_change_link = True
    autocomplete_fields = ("restaurant",)

class PhotoInline(admin.TabularInline):
    model = RestaurantPhoto
    fields = ("source", "remote_url", "photo_reference", "file", "width", "height", "collected_at")
    readonly_fields = ("collected_at",)
    extra = 0
    show_change_link = True
    autocomplete_fields = ("restaurant",)

class ReviewInline(admin.StackedInline):
    """評論文字較長，用 Stacked 版面較好讀；量很大時可改 Tabular。"""
    model = RestaurantReview
    fields = ("author_name", "author_url", "rating", "published_at", "text", "category_scores")
    extra = 0
    show_change_link = True
    autocomplete_fields = ("restaurant",)

class SourceMetaInline(admin.TabularInline):
    model = RestaurantSourceMeta
    fields = ("source", "fetched_at", "status_code", "quota_cost", "etag")
    readonly_fields = ("fetched_at",)
    extra = 0
    show_change_link = True
    autocomplete_fields = ("restaurant",)

# ========== Restaurant ==========
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        "name", "place_id", "formatted_address",
        "rating", "user_ratings_total", "price_level",
        "business_status", "open_status",
        "last_fetched_at",
    )
    search_fields = ("name", "place_id", "formatted_address")
    list_filter = ("business_status", "open_status", "price_level")
    ordering = ("-last_fetched_at", "name")
    readonly_fields = ("first_seen_at",)
    inlines = (OpeningHourInline, AttributeInline, PhotoInline, ReviewInline, SourceMetaInline)
    list_per_page = 50

# ========== 其他模型各自列表頁 ==========
@admin.register(RestaurantOpeningHour)
class RestaurantOpeningHourAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "weekday", "open_time", "close_time", "crosses_midnight")
    list_filter = ("weekday", "crosses_midnight")
    search_fields = ("restaurant__name", "restaurant__place_id")
    autocomplete_fields = ("restaurant",)
    ordering = ("restaurant__name", "weekday")

@admin.register(RestaurantPhoto)
class RestaurantPhotoAdmin(admin.ModelAdmin):
    def _preview(self, obj):
        if obj.remote_url:
            return format_html('<a href="{}" target="_blank">開啟</a>', obj.remote_url)
        return ""
    _preview.short_description = "預覽"

    list_display = ("restaurant", "source", "_preview", "width", "height", "collected_at")
    list_filter = ("source",)
    search_fields = ("restaurant__name", "restaurant__place_id", "remote_url", "photo_reference")
    autocomplete_fields = ("restaurant",)
    readonly_fields = ("collected_at",)
    ordering = ("-collected_at",)

@admin.register(RestaurantReview)
class RestaurantReviewAdmin(admin.ModelAdmin):
    @admin.display(description="內容")
    def short_text(self, obj):
        t = (obj.text or "").replace("\n", " ")
        return (t[:60] + "…") if len(t) > 60 else t

    list_display = ("restaurant", "author_name", "rating", "published_at", "short_text")
    list_filter = ("rating",)
    search_fields = ("author_name", "text", "restaurant__name", "restaurant__place_id")
    autocomplete_fields = ("restaurant",)
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-id")
    list_per_page = 50

@admin.register(RestaurantAttribute)
class RestaurantAttributeAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "key", "value", "source")
    list_filter = ("source", "key")
    search_fields = ("restaurant__name", "restaurant__place_id", "key", "value")
    autocomplete_fields = ("restaurant",)

@admin.register(RestaurantSourceMeta)
class RestaurantSourceMetaAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "source", "fetched_at", "status_code", "quota_cost", "etag")
    list_filter = ("source", "status_code")
    search_fields = ("restaurant__name", "restaurant__place_id", "etag")
    autocomplete_fields = ("restaurant",)
    date_hierarchy = "fetched_at"
    ordering = ("-fetched_at",)

@admin.register(RestaurantIndicatorDetail)
class RestaurantIndicatorDetailAdmin(admin.ModelAdmin):
    list_display = ("place_id", "indicator_type", "score", "source", "source_id", "created_at")
    list_filter = ("indicator_type", "source")
    search_fields = ("place_id", "indicator_type", "source")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

@admin.register(RestaurantIndicatorSummary)
class RestaurantIndicatorSummaryAdmin(admin.ModelAdmin):
    list_display = ("place_id", "indicator_type", "total_score", "count", "updated_at")
    list_filter = ("indicator_type",)
    search_fields = ("place_id", "indicator_type")
    date_hierarchy = "updated_at"
    ordering = ("-updated_at",)
