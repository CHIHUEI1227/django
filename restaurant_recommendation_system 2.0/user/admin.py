# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Profile, Announcement, FavoriteRestaurant, Follow,
    BusinessVerification, Notification, Report,
    UserPreference, UserPreferenceDetail, UserPreferenceSummary
)

# ------------------------
# Profile as User inline
# ------------------------
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = "user"
    extra = 0
    fields = (
        "profile_pic",
        "bio",
        "favorite_foods",
        "food_restrictions",
        "user_type",
        "verification_status",
        "business_name",
        "business_address",
        "business_phone",
    )

class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]

# 先把預設的 UserAdmin 移除再註冊我們的
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)


# ------------------------
# Announcement
# ------------------------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title", "announcement_type",
        "is_active", "is_pinned", "is_valid_badge",
        "start_date", "end_date",
        "created_by", "created_at"
    )
    list_filter = ("announcement_type", "is_active", "is_pinned", "created_at")
    search_fields = ("title", "content", "created_by__username")
    list_editable = ("is_active", "is_pinned")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at",)

    @admin.display(description="有效期內")
    def is_valid_badge(self, obj: Announcement):
        ok = obj.is_valid()
        color = "#1f883d" if ok else "#8a2d2d"
        text = "是" if ok else "否"
        return format_html('<b style="color:{}">{}</b>', color, text)

    def save_model(self, request, obj, form, change):
        # 預設建立者為當前使用者（建立時才補）
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ------------------------
# FavoriteRestaurant
# ------------------------
@admin.register(FavoriteRestaurant)
class FavoriteRestaurantAdmin(admin.ModelAdmin):
    list_display = (
        "user", "restaurant_name", "thumb", "maps_link",
        "restaurant_rating", "restaurant_price_level",
        "created_at",
    )
    list_filter = ("created_at", "restaurant_price_level")
    search_fields = ("user__username", "restaurant_name", "restaurant_place_id", "restaurant_address")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)

    @admin.display(description="預覽")
    def thumb(self, obj):
        if obj.restaurant_image_url:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:6px;" />',
                obj.restaurant_image_url
            )
        return "-"

    @admin.display(description="Google Maps")
    def maps_link(self, obj):
        if obj.restaurant_place_id:
            url = f"https://www.google.com/maps/place/?q=place_id:{obj.restaurant_place_id}"
            return format_html('<a href="{}" target="_blank">開啟</a>', url)
        if obj.restaurant_lat and obj.restaurant_lng:
            url = f"https://www.google.com/maps?q={obj.restaurant_lat},{obj.restaurant_lng}"
            return format_html('<a href="{}" target="_blank">開啟</a>', url)
        return "-"


# ------------------------
# Follow
# ------------------------
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed", "created_at")
    list_filter = ("created_at",)
    search_fields = ("follower__username", "followed__username")
    autocomplete_fields = ("follower", "followed")
    readonly_fields = ("created_at",)


# ------------------------
# BusinessVerification
# ------------------------
@admin.register(BusinessVerification)
class BusinessVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "business_name", "user", "status",
        "submitted_at", "reviewed_by", "reviewed_at",
    )
    list_filter = ("status", "submitted_at", "reviewed_at")
    search_fields = ("business_name", "business_registration_number", "user__username", "business_email")
    autocomplete_fields = ("user", "reviewed_by")
    readonly_fields = ("submitted_at", "reviewed_at")

    fieldsets = (
        ("申請資料", {
            "fields": ("user", "business_name", "business_registration_number",
                       "business_address", "business_phone", "business_email",
                       "registration_document", "additional_notes")
        }),
        ("審查", {
            "fields": ("status", "reviewed_by", "reviewed_at", "review_notes")
        }),
        ("時間", {
            "fields": ("submitted_at",),
        }),
    )

    # 動作：通過、拒絕、處理中
    @admin.action(description="標記為『已驗證』並更新 Profile")
    def approve(self, request, queryset):
        self._bulk_set_status(request, queryset, "verified")

    @admin.action(description="標記為『已拒絕』並更新 Profile")
    def reject(self, request, queryset):
        self._bulk_set_status(request, queryset, "rejected")

    @admin.action(description="標記為『處理中』")
    def mark_processing(self, request, queryset):
        count = queryset.update(status="processing", reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f"已標記 {count} 筆為『處理中』。")

    actions = ("approve", "reject", "mark_processing")

    def _bulk_set_status(self, request, queryset, to_status: str):
        updated = 0
        for obj in queryset.select_related("user"):
            obj.status = to_status
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save(update_fields=["status", "reviewed_by", "reviewed_at"])

            # 同步 Profile.verification_status
            try:
                profile = obj.user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=obj.user)
            profile.verification_status = to_status
            profile.user_type = "business" if to_status == "verified" else profile.user_type
            profile.save(update_fields=["verification_status", "user_type"])
            updated += 1
        self.message_user(request, f"已更新 {updated} 筆申請為『{to_status}』並同步 Profile。")

    def save_model(self, request, obj, form, change):
        # 只要狀態非 pending，補審核者與時間
        if obj.status in ("verified", "rejected", "processing"):
            if not obj.reviewed_by:
                obj.reviewed_by = request.user
            if not obj.reviewed_at:
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
        # 同步 Profile
        try:
            profile = obj.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=obj.user)
        profile.verification_status = obj.status
        if obj.status == "verified":
            profile.user_type = "business"
        profile.save(update_fields=["verification_status", "user_type"])


# ------------------------
# Notification
# ------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "sender", "is_read", "created_at", "short_message")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("recipient__username", "sender__username", "message")
    autocomplete_fields = ("recipient", "sender", "post", "comment")
    readonly_fields = ("created_at",)

    @admin.display(description="內容")
    def short_message(self, obj):
        s = (obj.message or "").strip()
        return s if len(s) <= 40 else s[:37] + "…"

    @admin.action(description="標記為已讀")
    def mark_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f"已標記 {count} 則為已讀")

    @admin.action(description="標記為未讀")
    def mark_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f"已標記 {count} 則為未讀")

    actions = ("mark_read", "mark_unread")


# ------------------------
# Report
# ------------------------
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "report_type", "status", "reporter", "reported_user",
                    "post", "comment", "created_at", "handled_by")
    list_filter = ("report_type", "status", "created_at")
    search_fields = ("reporter__username", "reported_user__username", "reason", "admin_notes")
    autocomplete_fields = ("reporter", "reported_user", "post", "comment", "handled_by")
    readonly_fields = ("created_at", "handled_at")

    @admin.action(description="標記為『處理中』")
    def mark_processing(self, request, queryset):
        count = queryset.update(status="processing", handled_by=request.user, handled_at=timezone.now())
        self.message_user(request, f"已標記 {count} 筆為處理中")

    @admin.action(description="標記為『已解決』")
    def mark_resolved(self, request, queryset):
        count = queryset.update(status="resolved", handled_by=request.user, handled_at=timezone.now())
        self.message_user(request, f"已標記 {count} 筆為已解決")

    @admin.action(description="標記為『已拒絕』")
    def mark_rejected(self, request, queryset):
        count = queryset.update(status="rejected", handled_by=request.user, handled_at=timezone.now())
        self.message_user(request, f"已標記 {count} 筆為已拒絕")

    actions = ("mark_processing", "mark_resolved", "mark_rejected")

    def save_model(self, request, obj, form, change):
        # 若管理員在表單直接改狀態，也自動填處理者/時間
        if obj.status in ("processing", "resolved", "rejected") and not obj.handled_by:
            obj.handled_by = request.user
            obj.handled_at = timezone.now()
        super().save_model(request, obj, form, change)


# ------------------------
# UserPreference & Details & Summary
# ------------------------
@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_price_level", "updated_at")
    list_filter = ("preferred_price_level", "updated_at")
    search_fields = ("user__username", "favorite_foods", "cuisine_preferences", "food_restrictions")
    autocomplete_fields = ("user",)
    readonly_fields = ("updated_at",)


@admin.register(UserPreferenceDetail)
class UserPreferenceDetailAdmin(admin.ModelAdmin):
    list_display = ("user", "keyword", "preference_type", "weight", "frequency", "source", "last_updated")
    list_filter = ("preference_type", "source", "last_updated")
    search_fields = ("user__username", "keyword")
    autocomplete_fields = ("user",)
    list_editable = ("weight",)

    @admin.action(description="權重 -0.1（衰減一次）")
    def decay_once(self, request, queryset):
        changed = 0
        for obj in queryset:
            obj.weight = max(obj.weight - 0.1, 0.1)
            obj.save(update_fields=["weight"])
            changed += 1
        self.message_user(request, f"已衰減 {changed} 筆權重")

    actions = ("decay_once",)


@admin.register(UserPreferenceSummary)
class UserPreferenceSummaryAdmin(admin.ModelAdmin):
    list_display = ("user", "preference_type", "preference_value", "total_score", "count", "try_count", "updated_at")
    list_filter = ("preference_type", "updated_at")
    search_fields = ("user__username", "preference_value")
    autocomplete_fields = ("user",)
    readonly_fields = ("updated_at",)

