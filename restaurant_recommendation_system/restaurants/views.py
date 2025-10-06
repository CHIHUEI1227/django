from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import Restaurant, RestaurantAttribute
from django.db.models import Q

def search_restaurants(request):
    query = request.GET.get('q', '').strip()
    restaurants = Restaurant.objects.none()
    if query:
        # 搜尋 name、address
        q1 = Q(name__icontains=query) | Q(formatted_address__icontains=query)
        # 搜尋 RestaurantAttribute 的 key 或 value
        attr_restaurant_ids = RestaurantAttribute.objects.filter(
            Q(key__icontains=query) | Q(value__icontains=query)
        ).values_list('restaurant_id', flat=True)
        q2 = Q(id__in=attr_restaurant_ids)
        # 合併條件
        restaurants = Restaurant.objects.filter(q1 | q2).distinct()
    else:
        restaurants = Restaurant.objects.all()[:10]  # 預設顯示前10筆

    restaurant_list = []
    for r in restaurants:
        # 取最新一張圖片
        photo = r.photos.first()  # 這裡就是根據 restaurant_id 取第一筆
        image_url = ""
        if photo:
            image_url = photo.file.url if photo.file else (photo.remote_url or "")
        restaurant_list.append({
            'id': r.id,
            'name': r.name,
            'address': r.formatted_address,
            'description': getattr(r, 'description', ''),
            'website': getattr(r, 'website', ''),
            'image_url': image_url,
        })

    context = {
        'restaurants': restaurant_list,
        'request': request,
    }
    return render(request, 'restaurant/search_restaurants.html', context)

def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    return render(request, 'restaurant/restaurant_detail.html', {'restaurant': restaurant})
