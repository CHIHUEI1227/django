from user.models import Notification

def notification_context(request):
    """
    上下文處理器：提供用戶未讀通知計數
    """
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    return {
        'unread_notifications_count': unread_count
    } 