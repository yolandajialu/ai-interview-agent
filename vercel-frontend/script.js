document.getElementById('userForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const userData = {
        role: formData.get('role'),
        experience_years: parseInt(formData.get('experience_years')),
        industry: formData.get('industry'),
        sales_stage: formData.get('sales_stage'),
        task_focus: formData.get('task_focus')
    };

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '正在启动AI访谈...';

    try {
        const response = await fetch(window.API_BASE_URL + '/api/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });

        const result = await response.json();

        if (result.success) {
            localStorage.setItem('interview_session_id', result.session_id);

            window.location.href = `/interview.html?session_id=${result.session_id}&question=${encodeURIComponent(result.question)}`;
        } else {
            alert('启动失败：' + result.error);
            submitBtn.disabled = false;
            submitBtn.textContent = '开始访谈 ✨';
        }
    } catch (error) {
        alert('网络错误：' + error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = '开始访谈 ✨';
    }
});
