// 在浏览器控制台（F12）中执行以下代码

console.log('=== PaperHub AI 配置诊断 ===\n');

// 1. 检查 localStorage
console.log('1. LocalStorage 配置:');
const aiConfigs = localStorage.getItem('aiConfigs');
const lastProvider = localStorage.getItem('lastAiProvider');
console.log('   lastAiProvider:', lastProvider);
console.log('   aiConfigs:', aiConfigs ? JSON.parse(aiConfigs) : '未设置');

// 2. 从后端获取配置
console.log('\n2. 从后端获取配置...');
fetch('/api/ai/config')
  .then(response => response.json())
  .then(data => {
    console.log('   后端配置:', data);
    
    if (data.has_api_key) {
      console.log('   ✅ 后端已配置 API Key');
      console.log('   Provider:', data.provider);
      console.log('   Base URL:', data.base_url);
      console.log('   Model ID:', data.model_id);
    } else {
      console.log('   ❌ 后端未配置 API Key');
    }
  })
  .catch(error => {
    console.error('   ❌ 请求失败:', error);
  });

console.log('\n3. 建议操作:');
console.log('   - 如果 localStorage 为空，这是正常的');
console.log('   - 前端会从后端 API 加载配置并显示');
console.log('   - 点击「配置」按钮后，配置会自动保存到 localStorage');
console.log('   - 下次打开时会优先从 localStorage 读取');
