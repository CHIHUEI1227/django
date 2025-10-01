from django.core.management.base import BaseCommand
from user.models import Profile
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = '修復商家用戶的驗證狀態'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='預覽將更改的資料但不實際修改')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # 獲取所有商家用戶
        business_profiles = Profile.objects.filter(user_type='business')
        
        self.stdout.write(self.style.SUCCESS(f'找到 {business_profiles.count()} 個商家用戶'))
        
        # 統計信息
        verified_count = 0
        unverified_count = 0
        pending_count = 0
        fixed_count = 0
        
        # 遍歷並檢查每個商家用戶
        for profile in business_profiles:
            original_status = profile.verification_status
            
            # 計算狀態
            if original_status == 'verified':
                verified_count += 1
            elif original_status == 'unverified':
                unverified_count += 1
            elif original_status == 'pending':
                pending_count += 1
            
            # 檢查問題：如果是商家但不是正確的狀態
            if original_status not in ['unverified', 'pending', 'verified', 'rejected']:
                self.stdout.write(f'發現問題: 用戶 {profile.user.username} 是商家但狀態為 "{original_status}"')
                
                if not dry_run:
                    profile.verification_status = 'unverified'
                    profile.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  - 已修復: 將用戶 {profile.user.username} 的狀態從 "{original_status}" 改為 "unverified"'))
        
        # 輸出統計信息
        self.stdout.write(self.style.SUCCESS('===== 統計信息 ====='))
        self.stdout.write(f'已驗證商家: {verified_count}')
        self.stdout.write(f'未驗證商家: {unverified_count}')
        self.stdout.write(f'審核中商家: {pending_count}')
        self.stdout.write(f'已修復商家: {fixed_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('這是預覽模式，未實際修改數據。如需修改，請移除 --dry-run 參數。'))
        else:
            self.stdout.write(self.style.SUCCESS('資料修復完成!')) 