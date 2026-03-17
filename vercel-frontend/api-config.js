// API配置文件
// 用于不同环境的API地址切换

(function() {
    // 检测当前环境
    const isLocalhost = window.location.hostname === 'localhost' ||
                        window.location.hostname === '127.0.0.1';

    // API基础URL配置
    const API_BASE_URL = isLocalhost
        ? 'http://127.0.0.1:8000'  // 本地开发环境
        : '';  // Render生产环境（待部署后替换为实际地址）

    // 将API配置挂载到window对象，方便其他脚本使用
    window.API_BASE_URL = API_BASE_URL;

    // 开发环境下打印配置信息
    if (isLocalhost) {
        console.log('🔧 本地开发模式');
        console.log('API地址:', API_BASE_URL);
    } else {
        console.log('🚀 生产模式');
        console.log('API地址:', API_BASE_URL);
    }
})();
