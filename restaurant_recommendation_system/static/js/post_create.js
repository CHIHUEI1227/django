let uploadedImages = [];

function renderPreviews() {
    const preview = document.getElementById('image-preview');
    preview.innerHTML = '';
    uploadedImages.forEach((file, idx) => {
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.marginRight = '12px';
        wrapper.style.marginBottom = '12px';

        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.style.maxWidth = '120px';
        img.style.borderRadius = '8px';
        img.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
        img.style.display = 'block';

        // 刪除按鈕
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.innerHTML = '&times;';
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
        removeBtn.onclick = () => {
            uploadedImages.splice(idx, 1);
            renderPreviews();
        };

        wrapper.appendChild(img);
        wrapper.appendChild(removeBtn);
        preview.appendChild(wrapper);
    });
}

document.getElementById('image-upload').addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    // 只加入還沒超過三張的部分
    const canAdd = Math.max(0, 3 - uploadedImages.length);
    uploadedImages = uploadedImages.concat(files.slice(0, canAdd));
    renderPreviews();
    // 清空 input 以便重複選同一張
    e.target.value = '';
});