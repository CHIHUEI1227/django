let uploadedImages = [];

// 新圖片預覽渲染與刪除（建立/編輯貼文都可用）
function renderPreviews() {
    const preview = document.getElementById('image-preview');
    preview.innerHTML = '';
    uploadedImages.forEach((file, idx) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'image-preview-wrapper';
        wrapper.style.position = 'relative';
        wrapper.style.marginRight = '12px';
        wrapper.style.marginBottom = '12px';

        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.style.maxWidth = '120px';
        img.style.borderRadius = '8px';
        img.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
        img.style.display = 'block';

        // 刪除按鈕（事件委派用 class）
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.innerHTML = '&times;';
        removeBtn.className = 'delete-new-image-btn delete-label';
        removeBtn.dataset.idx = idx;
        removeBtn.style.position = 'absolute';
        removeBtn.style.top = '4px';
        removeBtn.style.right = '4px';
        removeBtn.style.background = 'rgba(0,0,0,0.6)';
        removeBtn.style.color = '#fff';
        removeBtn.style.border = 'none';
        removeBtn.style.borderRadius = '50%';
        removeBtn.style.width = '24px';
        removeBtn.style.height = '24px';
        removeBtn.style.cursor = 'pointer';

        wrapper.appendChild(img);
        wrapper.appendChild(removeBtn);
        preview.appendChild(wrapper);
    });
}

// 新圖片預覽刪除（事件委派，動態產生也可用）
document.getElementById('image-preview')?.addEventListener('click', function(e) {
    if (e.target.classList.contains('delete-new-image-btn')) {
        const idx = parseInt(e.target.dataset.idx);
        uploadedImages.splice(idx, 1);
        renderPreviews();
    }
});

// 新圖片選擇
document.getElementById('image-upload')?.addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    const canAdd = Math.max(0, 3 - uploadedImages.length);
    uploadedImages = uploadedImages.concat(files.slice(0, canAdd));
    renderPreviews();
    e.target.value = '';
});

// 表單送出
document.getElementById('post-form')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    console.log('送出前 uploadedImages:', uploadedImages); // ← 送出前 log
    uploadedImages.forEach(file => {
        formData.append('images', file);
    });
    // 檢查 FormData 是否有 images 欄位
    for (let pair of formData.entries()) {
        if (pair[0] === 'images') {
            console.log('FormData images:', pair[1]);
        }
    }
    fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    }).then(res => {
        console.log('送出後 fetch response:', res); // ← 送出後 log
        if (res.redirected) {
            window.location.href = res.url;
        } else if (res.status === 302) {
            window.location.href = res.headers.get('Location');
        } else {
            res.text().then(text => {
                alert('貼文送出失敗，請稍後再試');
            });
        }
    });
});

// 舊圖片刪除（事件委派，edit_post.html用）
document.getElementById('old-image-preview')?.addEventListener('click', function(e) {
    if (e.target.classList.contains('delete-old-image-btn')) {
        const wrapper = e.target.closest('.image-preview-wrapper');
        wrapper.querySelector('input[type="checkbox"]').checked = true;
        wrapper.style.display = 'none';
    }
});