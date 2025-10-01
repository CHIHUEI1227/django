from django import forms
from post.models import Post, Comment

# 主類型（大類）
PRIMARY_CATEGORY_CHOICES = [
    ('', '請選擇餐廳主類型'),
    ('中式料理', '中式料理'),
    ('日式料理', '日式料理'),
    ('韓式料理', '韓式料理'),
    ('義式料理', '義式料理'),
    ('美式料理', '美式料理'),
    ('法式料理', '法式料理'),
    ('德式料理', '德式料理'),
    ('火鍋', '火鍋'),
    ('燒烤/BBQ', '燒烤/BBQ'),
    ('甜點/冰品', '甜點/冰品'),
    ('速食', '速食'),
    ('素食/蔬食', '素食/蔬食'),
    ('小吃/夜市', '小吃/夜市'),
    ('便當/自助餐', '便當/自助餐'),
    ('咖啡廳', '咖啡廳'),
    ('餐酒館/酒吧', '餐酒館/酒吧'),
    ('海鮮料理', '海鮮料理'),
    ('異國料理', '異國料理'),
    ('其他', '其他（請自行輸入）'),
]

# 細項對應表
SUBCATEGORY_MAP = {
    '中式料理': ['小吃店', '夜市小吃', '滷味', '鹽酥雞', '燒臘', '粥', '餛飩', '肉圓', '蚵仔煎', '炒飯', '炒麵', '魯肉飯', '豆花', '臭豆腐', '雞排', '蚵仔麵線', '肉羹', '米粉湯'],
    '日式料理': ['壽司', '拉麵', '居酒屋', '燒肉', '定食', '日式燒烤', '壽喜燒'],
    '韓式料理': ['韓式烤肉', '韓式小吃', '部隊鍋', '韓式燒烤'],
    '義式料理': ['義大利麵', '披薩'],
    '美式料理': ['美式餐廳', '漢堡', '美式BBQ'],
    '法式料理': ['法式餐廳'],
    '德式料理': ['德式餐廳'],
    '火鍋': ['火鍋', '麻辣火鍋', '涮涮鍋'],
    '燒烤/BBQ': ['燒烤店', '串燒', '碳烤', '炭火燒烤', '烤魚', '烤肉'],
    '甜點/冰品': ['甜點', '冰品'],
    '速食': ['速食', '炸雞'],
    '素食/蔬食': ['素食餐廳'],
    '小吃/夜市': ['小吃店', '夜市小吃'],
    '便當/自助餐': ['便當店', '自助餐'],
    '咖啡廳': ['咖啡廳', '早午餐'],
    '餐酒館/酒吧': ['餐酒館', '酒吧'],
    '海鮮料理': ['海鮮餐廳', '海鮮'],
    '異國料理': ['泰式料理', '越南料理', '印度料理', '墨西哥/拉美料理', '其他異國料理'],
    '其他': ['其他'],
}

class PostCreateForm(forms.ModelForm):
    primary_category = forms.ChoiceField(
        label="餐廳主類型",
        choices=PRIMARY_CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={'onchange': 'updateSubcategoryOptions(this.value);'})
    )
    restaurant_type = forms.ChoiceField(
        label="細項分類",
        choices=[('', '請先選擇餐廳主類型')],
        required=True,
        widget=forms.Select()
    )
    meal_time = forms.ChoiceField(
        label="用餐時段",
        choices=Post.MEAL_TIME_CHOICES,
        required=True,
        widget=forms.Select()
    )
    dining_date = forms.DateField(
        label="用餐日期",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Post
        fields = [
            'title', 'content', 'location_name', 'location_address',
            'location_lat', 'location_lng', 'location_place_id',
            'restaurant_type', 'meal_time', 'dining_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '請輸入標題'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': '分享您的美食經驗...'}),
            'location_name': forms.TextInput(attrs={'placeholder': '餐廳名稱', 'id': 'location-name', 'readonly': 'readonly'}),
            'location_address': forms.TextInput(attrs={'placeholder': '餐廳地址', 'id': 'location-address', 'readonly': 'readonly'}),
            'location_lat': forms.HiddenInput(attrs={'id': 'location-lat'}),
            'location_lng': forms.HiddenInput(attrs={'id': 'location-lng'}),
            'location_place_id': forms.HiddenInput(attrs={'id': 'location-place-id'}),
            'meal_time': forms.Select(attrs={'id': 'meal-time'}),
            'dining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'title': '標題',
            'content': '內容',
            'location_name': '餐廳名稱',
            'location_address': '餐廳地址',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = "標題"
        self.fields['content'].label = "內容"
        self.fields['location_name'].label = "餐廳名稱 (可選)"
        self.fields['location_address'].label = "餐廳地址 (可選)"
        self.fields['location_lat'].widget = forms.HiddenInput()
        self.fields['location_lng'].widget = forms.HiddenInput()
        self.fields['location_place_id'].widget = forms.HiddenInput()
        # 動態設定細項分類選單
        if 'primary_category' in self.data:
            selected = self.data.get('primary_category')
            sub_choices = SUBCATEGORY_MAP.get(selected, [('', '無細項')])
            self.fields['restaurant_type'].choices = [('', '請選擇細項')] + [(s, s) for s in sub_choices]
        elif self.instance and hasattr(self.instance, 'primary_category'):
            sub_choices = SUBCATEGORY_MAP.get(self.instance.primary_category, [('', '無細項')])
            self.fields['restaurant_type'].choices = [('', '請選擇細項')] + [(s, s) for s in sub_choices]
        else:
            self.fields['restaurant_type'].choices = [('', '請先選擇餐廳主類型')]
        # 初始化細項分類選單的值
        if 'restaurant_type' in self.fields and self.instance and self.instance.pk:
            self.fields['restaurant_type'].widget.attrs['data-current-value'] = self.instance.restaurant_type or ''
        # 如果 instance 有 restaurant_type 但 primary_category 沒有，反推主類型
        if self.instance and self.instance.pk and not getattr(self.instance, 'primary_category', None):
            rest_type = getattr(self.instance, 'restaurant_type', None)
            if rest_type:
                for cat, sublist in SUBCATEGORY_MAP.items():
                    if rest_type in sublist:
                        self.initial['primary_category'] = cat
                        break
class CommentForm(forms.ModelForm):
    """評論表單"""
    content = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'placeholder': '發表您的評論...',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Comment
        fields = ['content']