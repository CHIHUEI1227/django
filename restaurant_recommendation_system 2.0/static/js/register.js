/**
 * 註冊頁面的JavaScript功能
 */
document.addEventListener('DOMContentLoaded', function() {
    // 為表單輸入添加Bootstrap樣式
    const usernameField = document.getElementById('id_username');
    const emailField = document.getElementById('id_email');
    const password1Field = document.getElementById('id_password1');
    const password2Field = document.getElementById('id_password2');
    const businessFields = document.getElementById('business-fields');
    
    if(usernameField) {
        usernameField.classList.add('form-control');
        usernameField.setAttribute('placeholder', '選擇一個用戶名');
    }
    
    if(emailField) {
        emailField.classList.add('form-control');
        emailField.setAttribute('placeholder', '輸入您的電子郵件');
    }
    
    if(password1Field) {
        password1Field.classList.add('form-control');
        password1Field.setAttribute('placeholder', '創建一個密碼');
    }
    
    if(password2Field) {
        password2Field.classList.add('form-control');
        password2Field.setAttribute('placeholder', '再次輸入您的密碼');
    }
    
    // 為單選按鈕添加樣式和事件監聽
    const radioButtons = document.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(function(radio) {
        radio.classList.add('form-check-input');
        const label = radio.nextSibling;
        if(label) {
            label.classList.add('form-check-label');
        }
        
        // 當選擇變更時顯示/隱藏商家欄位
        radio.addEventListener('change', function() {
            if(businessFields) {
                if(radio.value === 'business' && radio.checked) {
                    businessFields.style.display = 'block';
                } else {
                    businessFields.style.display = 'none';
                }
            }
        });
    });

    // 檢查初始狀態 - 如果商家選項已被選中
    const businessRadio = document.querySelector('input[name="user_type"][value="business"]');
    if(businessRadio && businessRadio.checked && businessFields) {
        businessFields.style.display = 'block';
    }

    // 商家註冊處理
    const form = document.getElementById('registerForm');
    if(form) {
        form.addEventListener('submit', function(e) {
            // 檢查是否選擇了商家帳號類型
            if(businessRadio && businessRadio.checked) {
                // 儲存商家註冊標記，後端處理重定向
                localStorage.setItem('redirect_to_verification', 'true');
                console.log("正在提交商家註冊表單");
                // 提交表單後將由後端處理重定向到 apply_for_verification
            }
        });
    }
}); 