const axios = require('axios');

const API_KEY = process.env.OPENROUTER_API_KEY;
const BASE_URL = "https://openrouter.ai/api/v1/chat/completions";

const TEST_MODELS = [
  // MoA v2 付费模型
  { id: "moonshotai/kimi-k2.5", name: "Kimi 2.5", isFree: false },
  { id: "z-ai/glm-5", name: "GLM 5", isFree: false },
  { id: "minimax/minimax-m2.5", name: "MiniMax 2.5", isFree: false },
  
  // 备用付费模型
  { id: "openai/gpt-4o-mini", name: "GPT-4o Mini", isFree: false },
  { id: "anthropic/claude-3-haiku", name: "Claude 3 Haiku", isFree: false },
  { id: "google/gemini-2.0-flash-thinking-exp", name: "Gemini 2.0 Flash Thinking", isFree: false },
  
  // 免费模型（可能需要:free后缀）
  { id: "meta-llama/llama-3.3-70b-instruct:free", name: "Llama 3.3 70B Free", isFree: true },
  { id: "google/gemini-2.0-flash-exp:free", name: "Gemini 2.0 Flash Free", isFree: true },
  { id: "mistralai/mistral-small-24b-instruct-2501:free", name: "Mistral Small Free", isFree: true },
  
  // 测试带和不带:free后缀
  { id: "meta-llama/llama-3.3-70b-instruct", name: "Llama 3.3 70B (no suffix)", isFree: false },
  { id: "google/gemini-2.0-flash-exp", name: "Gemini 2.0 Flash (no suffix)", isFree: false },
];

async function testModel(model) {
  console.log(`\n🔍 测试模型: ${model.name} (${model.id})`);
  
  try {
    const startTime = Date.now();
    
    const response = await axios.post(BASE_URL, {
      model: model.id,
      messages: [{ role: "user", content: "请用一句话回复'连接成功'。" }],
      max_tokens: 10,
      temperature: 0.1
    }, {
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "HTTP-Referer": "https://github.com/openclaw/openclaw",
        "Content-Type": "application/json"
      },
      timeout: 30000  // 30秒超时
    });
    
    const elapsed = Date.now() - startTime;
    const content = response.data.choices[0].message.content;
    
    console.log(`✅ 成功! 耗时: ${elapsed}ms`);
    console.log(`   响应: "${content}"`);
    
    return {
      success: true,
      model: model.id,
      elapsed,
      content
    };
    
  } catch (error) {
    console.log(`❌ 失败: ${error.message}`);
    
    if (error.response) {
      console.log(`   状态码: ${error.response.status}`);
      console.log(`   错误详情: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    
    return {
      success: false,
      model: model.id,
      error: error.message,
      details: error.response?.data
    };
  }
}

async function checkAccountStatus() {
  console.log('📊 检查OpenRouter账户状态...');
  
  try {
    const response = await axios.get("https://openrouter.ai/api/v1/auth/key", {
      headers: {
        "Authorization": `Bearer ${API_KEY}`
      }
    });
    
    const data = response.data.data;
    console.log(`✅ 账户信息:`);
    console.log(`   - 标签: ${data.label.substring(0, 20)}...`);
    console.log(`   - 免费层级: ${data.is_free_tier ? '是' : '否'}`);
    console.log(`   - 总使用量: $${data.usage.toFixed(6)}`);
    console.log(`   - 今日使用: $${data.usage_daily.toFixed(6)}`);
    
    return data;
    
  } catch (error) {
    console.log(`❌ 账户状态检查失败: ${error.message}`);
    return null;
  }
}

async function main() {
  console.log('========================================');
  console.log('OpenRouter API 连接诊断');
  console.log('========================================');
  
  if (!API_KEY) {
    console.error('❌ 错误: OPENROUTER_API_KEY 环境变量未设置');
    process.exit(1);
  }
  
  console.log(`🔑 API密钥前20字符: ${API_KEY.substring(0, 20)}...`);
  
  // 检查账户状态
  const accountInfo = await checkAccountStatus();
  
  if (!accountInfo) {
    console.log('⚠️  无法获取账户信息，继续测试模型...');
  }
  
  // 测试所有模型
  console.log('\n========================================');
  console.log('测试模型连接');
  console.log('========================================');
  
  const results = [];
  
  for (const model of TEST_MODELS) {
    const result = await testModel(model);
    results.push(result);
    
    // 付费模型失败时，稍微等待避免速率限制
    if (!model.isFree && !result.success) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  // 汇总结果
  console.log('\n========================================');
  console.log('诊断结果汇总');
  console.log('========================================');
  
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);
  
  console.log(`✅ 成功: ${successful.length}/${TEST_MODELS.length}`);
  console.log(`❌ 失败: ${failed.length}/${TEST_MODELS.length}`);
  
  if (successful.length > 0) {
    console.log('\n可用的模型:');
    successful.forEach(r => {
      const model = TEST_MODELS.find(m => m.id === r.model);
      console.log(`  - ${model?.name || r.model} (${r.elapsed}ms)`);
    });
  }
  
  if (failed.length > 0) {
    console.log('\n失败的模型:');
    failed.forEach(r => {
      const model = TEST_MODELS.find(m => m.id === r.model);
      console.log(`  - ${model?.name || r.model}: ${r.error}`);
    });
  }
  
  // MoA v2 配置建议
  console.log('\n========================================');
  console.log('MoA v2 配置建议');
  console.log('========================================');
  
  const availablePaidModels = successful.filter(r => {
    const model = TEST_MODELS.find(m => m.id === r.model);
    return model && !model.isFree;
  });
  
  if (availablePaidModels.length >= 3) {
    console.log('✅ 建议使用原配置模型:');
    const moaModels = availablePaidModels.filter(r => 
      r.model.includes('kimi') || r.model.includes('glm') || r.model.includes('minimax')
    );
    
    if (moaModels.length >= 3) {
      moaModels.slice(0, 3).forEach(r => {
        const model = TEST_MODELS.find(m => m.id === r.model);
        console.log(`  - ${model?.name} (${r.model})`);
      });
    } else {
      console.log('⚠️  原MoA模型部分可用，建议改用以下模型:');
      availablePaidModels.slice(0, 3).forEach(r => {
        const model = TEST_MODELS.find(m => m.id === r.model);
        console.log(`  - ${model?.name} (${r.model})`);
      });
    }
  } else if (availablePaidModels.length > 0) {
    console.log(`⚠️  只有 ${availablePaidModels.length} 个付费模型可用，建议:`);
    console.log(`  1. 使用付费模型: ${availablePaidModels.map(r => {
      const model = TEST_MODELS.find(m => m.id === r.model);
      return model?.name;
    }).join(', ')}`);
    
    // 尝试补充免费模型
    const availableFreeModels = successful.filter(r => {
      const model = TEST_MODELS.find(m => m.id === r.model);
      return model && model.isFree;
    });
    
    if (availableFreeModels.length > 0) {
      const needed = 3 - availablePaidModels.length;
      const freeToUse = availableFreeModels.slice(0, needed);
      console.log(`  2. 补充免费模型: ${freeToUse.map(r => {
        const model = TEST_MODELS.find(m => m.id === r.model);
        return model?.name;
      }).join(', ')}`);
    }
  } else {
    console.log('❌ 无可用付费模型，需要检查账户权限或切换API提供商');
  }
}

main().catch(error => {
  console.error('诊断脚本执行失败:', error);
  process.exit(1);
});