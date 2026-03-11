const axios = require('axios');

const API_KEY = process.env.OPENROUTER_API_KEY;

async function analyzeModelResponse(modelId, modelName) {
  console.log(`\n🔬 分析 ${modelName} (${modelId}) 响应结构`);
  
  try {
    const response = await axios.post('https://openrouter.ai/api/v1/chat/completions', {
      model: modelId,
      messages: [{ role: 'user', content: '简单回答：什么是人工智能？' }],
      max_tokens: 100,
      temperature: 0.1
    }, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'HTTP-Referer': 'https://github.com/openclaw/openclaw',
        'Content-Type': 'application/json'
      },
      timeout: 20000
    });
    
    const data = response.data;
    const choice = data.choices[0];
    const message = choice.message;
    
    console.log('📊 完整响应结构:');
    console.log(JSON.stringify({
      model: data.model,
      provider: data.provider,
      finish_reason: choice.finish_reason,
      native_finish_reason: choice.native_finish_reason,
      message: {
        role: message.role,
        content: message.content,
        content_length: message.content ? message.content.length : 0,
        has_reasoning: !!message.reasoning,
        reasoning_length: message.reasoning ? message.reasoning.length : 0,
        has_reasoning_details: !!(message.reasoning_details && message.reasoning_details.length > 0),
        refusal: message.refusal
      },
      usage: data.usage
    }, null, 2));
    
    // 分析问题
    console.log('\n🔍 问题分析:');
    
    if (!message.content || message.content.trim() === '') {
      console.log('❌ 问题: content字段为空');
      
      if (message.reasoning && message.reasoning.trim() !== '') {
        console.log(`✅ 解决方案: 使用reasoning字段 (${message.reasoning.length}字符)`);
        console.log(`   内容示例: "${message.reasoning.substring(0, 100)}..."`);
      } else if (message.reasoning_details && message.reasoning_details.length > 0) {
        console.log(`✅ 解决方案: 使用reasoning_details (${message.reasoning_details.length}个项目)`);
        const text = message.reasoning_details.map(d => d.text).join('\n');
        console.log(`   内容示例: "${text.substring(0, 100)}..."`);
      } else {
        console.log('❌ 所有字段都为空，可能是模型配置问题');
      }
    } else {
      console.log(`✅ content字段正常 (${message.content.length}字符)`);
      console.log(`   内容: "${message.content.substring(0, 100)}..."`);
    }
    
    return { success: true, data: data };
    
  } catch (error) {
    console.log(`❌ API调用失败: ${error.message}`);
    if (error.response) {
      console.log('状态码:', error.response.status);
      console.log('错误详情:', JSON.stringify(error.response.data, null, 2));
    }
    return { success: false, error: error.message };
  }
}

async function main() {
  console.log('========================================');
  console.log('OpenRouter响应结构分析');
  console.log('========================================');
  
  if (!API_KEY) {
    console.error('❌ OPENROUTER_API_KEY未设置');
    process.exit(1);
  }
  
  console.log('API密钥:', API_KEY.substring(0, 20) + '...\n');
  
  // 分析三个MoA核心模型
  const models = [
    { id: 'moonshotai/kimi-k2.5', name: 'Kimi 2.5' },
    { id: 'z-ai/glm-5', name: 'GLM 5' },
    { id: 'minimax/minimax-m2.5', name: 'MiniMax 2.5' }
  ];
  
  for (const model of models) {
    await analyzeModelResponse(model.id, model.name);
    await new Promise(resolve => setTimeout(resolve, 2000)); // 等待2秒
  }
  
  console.log('\n========================================');
  console.log('基于图片的排查建议');
  console.log('========================================');
  console.log('📸 您提供的图片可能是OpenRouter控制台的以下内容:');
  console.log('');
  console.log('1. 🔧 模型配置页面检查:');
  console.log('   - 检查Kimi 2.5/GLM 5/MiniMax 2.5是否已启用');
  console.log('   - 查看是否有"推理模式(Reasoning)"开关');
  console.log('   - 确认模型配额是否充足');
  console.log('');
  console.log('2. ⚙️ API设置页面检查:');
  console.log('   - 确认API密钥权限是否正确');
  console.log('   - 检查是否开启了"流式响应"或其他高级功能');
  console.log('   - 查看请求频率限制设置');
  console.log('');
  console.log('3. 📊 响应格式问题排查:');
  console.log('   - 部分模型默认返回reasoning而非content');
  console.log('   - 需要在请求中添加参数控制响应格式');
  console.log('   - 或修改代码提取reasoning字段内容');
  console.log('');
  console.log('4. 🔄 MoA代码修复方案:');
  console.log('   - 已更新callOpenRouter函数处理reasoning字段');
  console.log('   - 可以尝试添加`include_reasoning: false`参数');
  console.log('   - 或使用其他不返回reasoning的模型');
  console.log('');
  console.log('💡 请告知图片的具体内容，以便精确排查:');
  console.log('   - 是模型列表页面？');
  console.log('   - 是API设置页面？');
  console.log('   - 是错误信息截图？');
  console.log('   - 是响应示例截图？');
}

main().catch(error => {
  console.error('分析失败:', error);
  process.exit(1);
});