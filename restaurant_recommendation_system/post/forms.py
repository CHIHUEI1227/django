from django import forms
from post.models import Post, Comment

class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'location_name', 'location_address', 'location_lat', 'location_lng', 'location_place_id']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '請輸入標題'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': '分享您的美食經驗...'}),
            'location_name': forms.TextInput(attrs={'placeholder': '餐廳名稱', 'id': 'location-name', 'readonly': 'readonly'}),
            'location_address': forms.TextInput(attrs={'placeholder': '餐廳地址', 'id': 'location-address', 'readonly': 'readonly'}),
            'location_lat': forms.HiddenInput(attrs={'id': 'location-lat'}),
            'location_lng': forms.HiddenInput(attrs={'id': 'location-lng'}),
            'location_place_id': forms.HiddenInput(attrs={'id': 'location-place-id'}),
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