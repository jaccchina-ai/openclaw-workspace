const axios = require('axios');

// 统一API调用函数
async function callOpenRouter(model, messages, maxTokens = 1200, timeout = 180000) {
  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
  const BASE_URL = "https://openrouter.ai/api/v1/chat/completions";
  
  try {
    const response = await axios.post(BASE_URL, {
      model: model,
      messages: messages,
      max_tokens: maxTokens
    }, {
      headers: {
        "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
        "HTTP-Referer": "https://github.com/openclaw/openclaw",
        "Content-Type": "application/json"
      },
      timeout: timeout
    });
    
    const choice = response.data.choices[0];
    const message = choice.message;
    
    // 处理可能的reasoning响应：优先使用content，其次使用reasoning
    let content = message.content;
    
    if (!content || content.trim() === '') {
      // 如果content为空，尝试使用reasoning字段
      if (message.reasoning && message.reasoning.trim() !== '') {
        content = message.reasoning;
        console.log(`[API] 使用reasoning字段代替空content (${model})`);
      } else if (message.reasoning_details && message.reasoning_details.length > 0) {
        // 或者使用reasoning_details
        content = message.reasoning_details.map(d => d.text).join('\n');
        console.log(`[API] 使用reasoning_details字段代替空content (${model})`);
      }
    }
    
    // 如果仍然没有内容，使用默认消息
    if (!content || content.trim() === '') {
      content = "[模型返回了空响应]";
      console.log(`[API] 警告: 模型返回空响应 (${model})`);
    }
    
    return { success: true, content: content };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.error?.message || error.message 
    };
  }
}

// Deepseek API调用函数
async function callDeepseek(messages, maxTokens = 2000, timeout = 180000) {
  const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
  const OPENAI_BASE_URL = process.env.OPENAI_BASE_URL || "https://api.deepseek.com/v1";
  
  if (!OPENAI_API_KEY) {
    return { 
      success: false, 
      error: "OPENAI_API_KEY environment variable not set for Deepseek" 
    };
  }
  
  try {
    const response = await axios.post(`${OPENAI_BASE_URL}/chat/completions`, {
      model: "deepseek-chat",  // 使用deepseek-chat，兼容性更好
      messages: messages,
      max_tokens: maxTokens,
      temperature: 0.3
    }, {
      headers: {
        "Authorization": `Bearer ${OPENAI_API_KEY}`,
        "Content-Type": "application/json"
      },
      timeout: timeout
    });
    return { success: true, content: response.data.choices[0].message.content };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.error?.message || error.message 
    };
  }
}

async function handle({ prompt, tier = 'paid', mode = 'enhanced' }) {
  // 1. Configuration
  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
  if (!OPENROUTER_API_KEY) {
    return "Error: OPENROUTER_API_KEY environment variable not set";
  }
  
  // Model tiers
  const MODELS = {
    paid: {
      proposers: [
        { id: "openai/gpt-4o-mini", name: "GPT-4o Mini" },
        { id: "anthropic/claude-3-haiku", name: "Claude 3 Haiku" },
        { id: "qwen/qwen-2.5-coder-32b-instruct", name: "Qwen 2.5 Coder 32B" },
        { id: "google/gemini-3-flash-preview", name: "Gemini 3 Flash Preview" }
      ],
      aggregator: { id: "openai/gpt-4o-mini", name: "GPT-4o Mini (Aggregator)" },
      maxTokens: 1200,
      crossReviewTokens: 1000,
      aggregatorMaxTokens: 3000
    },
    free: {
      proposers: [
        { id: "meta-llama/llama-3.3-70b-instruct", name: "Llama 3.3 70B" },
        { id: "openai/gpt-4o-mini", name: "GPT-4o Mini" },
        { id: "anthropic/claude-3-haiku", name: "Claude 3 Haiku" }
      ],
      aggregator: { id: "meta-llama/llama-3.3-70b-instruct", name: "Llama 3.3 70B (Aggregator)" },
      maxTokens: 800,
      crossReviewTokens: 600,
      aggregatorMaxTokens: 1500
    }
  };

  const config = MODELS[tier] || MODELS.paid;
  const { proposers, aggregator, maxTokens, crossReviewTokens, aggregatorMaxTokens } = config;

  console.log(`[MoA v2] Tier: ${tier.toUpperCase()} | Mode: ${mode.toUpperCase()}`);
  console.log(`[MoA v2] Prompt: "${prompt.substring(0, 80)}..."\n`);
  console.log(`[MoA v2] Models: ${proposers.map(p => p.name).join(', ')}`);
  console.log(`[MoA v2] Aggregator: ${aggregator.name}\n`);

  // ========== 第一阶段：独立方案 ==========
  console.log(`[MoA v2] 阶段 1/3: 独立方案生成`);
  console.log(`[MoA v2] 并行调用 ${proposers.length} 个模型...\n`);
  
  const phase1Results = [];
  const phase1Start = Date.now();
  
  for (const proposer of proposers) {
    const startTime = Date.now();
    console.log(`[MoA v2] 调用 ${proposer.name}...`);
    
    const result = await callOpenRouter(
      proposer.id,
      [{ role: "user", content: prompt }],
      maxTokens
    );
    
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    if (result.success) {
      console.log(`✓ ${proposer.name} 响应成功 (${elapsed}s)`);
      phase1Results.push({
        model: proposer,
        content: result.content,
        success: true
      });
    } else {
      console.log(`✗ ${proposer.name}: ${result.error}`);
      phase1Results.push({
        model: proposer,
        content: `Error: ${result.error}`,
        success: false
      });
    }
  }
  
  const phase1Success = phase1Results.filter(r => r.success).length;
  const phase1Elapsed = ((Date.now() - phase1Start) / 1000).toFixed(1);
  console.log(`\n[MoA v2] 阶段1完成: ${phase1Success}/${proposers.length} 成功 (${phase1Elapsed}s)`);
  
  if (phase1Success < 2) {
    console.log(`[MoA v2] 警告: 独立方案阶段成功模型少于2个，无法进行交叉评论`);
    // 回退到简单聚合模式
    return await fallbackSynthesis(prompt, phase1Results, aggregator, aggregatorMaxTokens);
  }
  
  // 根据模式选择执行路径
  if (mode === 'classic') {
    // 经典模式：直接聚合，不交叉评论，无Deepseek审核
    console.log(`\n[MoA v2] 经典模式：跳过交叉评论和Deepseek审核`);
    return await classicSynthesis(prompt, phase1Results, aggregator, aggregatorMaxTokens, tier, proposers);
  }
  
  // 增强模式：继续执行交叉评论和Deepseek审核
  // ========== 第二阶段：交叉评论 ==========
  console.log(`\n[MoA v2] 阶段 2/4: 交叉评论`);
  console.log(`[MoA v2] 每个模型评论其他模型的回答...\n`);
  
  const phase2Results = [];
  const phase2Start = Date.now();
  const successfulResponses = phase1Results.filter(r => r.success);
  
  for (const reviewer of successfulResponses) {
    const startTime = Date.now();
    console.log(`[MoA v2] ${reviewer.model.name} 正在评论其他模型...`);
    
    // 收集其他模型回答供评论
    const otherResponses = successfulResponses
      .filter(r => r.model.id !== reviewer.model.id)
      .map(r => `--- ${r.model.name} ---\n${r.content}`)
      .join('\n\n');
    
    const reviewPrompt = `
你是一位专业评论员，需要分析其他AI模型对以下问题的回答：

原始问题：
"${prompt}"

你的回答（供参考）：
${reviewer.content}

其他模型的回答：
${otherResponses}

请进行深入交叉评论：
1. 其他模型的回答有哪些优点和独到见解？
2. 哪些部分存在潜在偏见、错误或不一致？
3. 与你的回答相比，主要分歧点在哪里？
4. 哪些建议最具可行性和价值？
5. 指出需要特别注意的风险或限制。

请提供结构化的评论，重点分析质量、逻辑一致性和实际可行性。
`;
    
    const result = await callOpenRouter(
      reviewer.model.id,
      [{ role: "user", content: reviewPrompt }],
      crossReviewTokens
    );
    
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    if (result.success) {
      console.log(`✓ ${reviewer.model.name} 评论完成 (${elapsed}s)`);
      phase2Results.push({
        reviewer: reviewer.model,
        review: result.content,
        success: true
      });
    } else {
      console.log(`✗ ${reviewer.model.name} 评论失败: ${result.error}`);
      phase2Results.push({
        reviewer: reviewer.model,
        review: `Error: ${result.error}`,
        success: false
      });
    }
  }
  
  const phase2Elapsed = ((Date.now() - phase2Start) / 1000).toFixed(1);
  console.log(`\n[MoA v2] 阶段2完成: ${phase2Results.filter(r => r.success).length}/${successfulResponses.length} 成功 (${phase2Elapsed}s)`);
  
  // ========== 第三阶段：聚合与结构化报告 ==========
  console.log(`\n[MoA v2] 阶段 3/4: 聚合与结构化报告`);
  console.log(`[MoA v2] ${aggregator.name} 正在生成最终报告...\n`);
  
  const aggregationStart = Date.now();
  
  // 准备聚合提示
  const successfulReviews = phase2Results.filter(r => r.success);
  const reviewsText = successfulReviews.map(r => 
    `--- ${r.reviewer.name} 的评论 ---\n${r.review}`
  ).join('\n\n');
  
  const responsesText = successfulResponses.map(r => 
    `--- ${r.model.name} 的回答 ---\n${r.content}`
  ).join('\n\n');
  
  const aggregationPrompt = `
你是一位高级分析聚合专家，需要基于多AI模型辩论生成结构化决策报告。

原始问题：
"${prompt}"

========== 第一阶段：独立方案 ==========
${responsesText}

========== 第二阶段：交叉评论 ==========
${reviewsText}

========== 报告要求 ==========

请生成一份结构化报告，包含以下部分：

# 执行摘要
- 总体评估结论
- 关键发现摘要
- 置信度水平

# 关键共识点
- 列出所有模型一致同意的核心观点
- 共识的强度和理由

# 主要分歧点
- 详细描述不同模型之间的关键分歧
- 分析分歧的根源（数据偏见、方法论差异等）
- 评估每个立场的合理性

# 风险评估
- 识别潜在风险、限制和不确定性
- 评估每个风险的影响程度

# 建议与行动计划
- 基于共识和分歧分析提出具体建议
- 按优先级排序
- 明确下一步行动

# 需要人类审核的争议点
- 列出需要人工判断的争议问题
- 提供不同观点的权衡分析
- 建议审核重点

要求：
1. 保持客观中立，不偏袒任何特定模型
2. 基于证据和逻辑推理
3. 提供可操作的具体建议
4. 使用清晰的结构化格式
5. 突出显示最重要发现

请生成完整报告：
`;
  
  const aggregationResult = await callOpenRouter(
    aggregator.id,
    [{ role: "user", content: aggregationPrompt }],
    aggregatorMaxTokens
  );
  
  const aggregationElapsed = ((Date.now() - aggregationStart) / 1000).toFixed(1);
  
  if (aggregationResult.success) {
    console.log(`✓ ${aggregator.name} 报告生成成功 (${aggregationElapsed}s)`);
    
    // ========== 第四阶段：Deepseek独立审核 ==========
    console.log(`\n[MoA v2] 阶段 4/4: Deepseek独立审核`);
    console.log(`[MoA v2] Deepseek 正在审核报告...\n`);
    
    const auditStart = Date.now();
    
    const auditPrompt = `
你是一位独立的AI审计专家，负责审核一份由多个AI模型辩论生成的分析报告。

审核任务：
你将以"人类立场"的视角，审查以下报告的质量、客观性和实用性，发现可能被OpenRouter模型忽略的盲点。

========== 原始问题 ==========
"${prompt}"

========== 待审核的报告 ==========
${aggregationResult.content}

========== 审核要求 ==========

请提供结构化审核意见，包含以下部分：

# 报告质量评估
- 逻辑一致性和连贯性评分（1-10分）
- 证据充分性和数据支持程度
- 结构完整性和可读性

# 潜在偏见识别
- 识别报告可能存在的模型偏见（文化、训练数据、方法论等）
- 检查是否过度偏袒某个特定模型的观点
- 评估风险识别是否充分全面

# 盲点与遗漏分析
- 指出报告中可能遗漏的重要角度或考虑因素
- 识别OpenRouter模型可能存在的共同盲点
- 补充需要关注但未提及的关键问题

# 实用性改进建议
- 针对报告的可操作性提出具体改进建议
- 指出需要进一步验证或数据支持的结论
- 提供增强报告实用性的具体方法

# 最终审核结论
- 整体可信度评估（高/中/低）
- 是否推荐采纳此报告建议
- 最重要的1-3个注意事项

要求：
1. 保持客观、批判性但建设性的态度
2. 聚焦于报告内容本身，而非原始问题
3. 提供具体的改进建议，而非泛泛而谈
4. 从"人类立场"出发，考虑实际应用场景
5. 关注报告的实用性和风险控制

请生成独立审核报告：
`;
    
    const auditResult = await callDeepseek(
      [{ role: "user", content: auditPrompt }],
      2500  // Deepseek审核可以使用更多token
    );
    
    const auditElapsed = ((Date.now() - auditStart) / 1000).toFixed(1);
    
    if (auditResult.success) {
      console.log(`✓ Deepseek 审核完成 (${auditElapsed}s)`);
      
      // 添加执行摘要
      const totalElapsed = ((Date.now() - phase1Start) / 1000).toFixed(1);
      const summary = `
============================================================
MoA v2 结构化报告 (${tier.toUpperCase()} TIER)
============================================================

📊 执行统计：
- 总耗时: ${totalElapsed}秒
- 独立方案: ${phase1Success}/${proposers.length} 成功
- 交叉评论: ${successfulReviews.length}/${successfulResponses.length} 成功
- 总API调用: ${proposers.length + successfulResponses.length + 2}次
- 聚合模型: ${aggregator.name}
- 审核模型: Deepseek (OpenClaw)

💡 提示：此报告基于四阶段AI协作工作流生成，包含：
  1. ${proposers.map(p => p.name).join('、')}的独立分析
  2. 模型间的交叉评论和批评
  3. ${aggregator.name}的综合评估
  4. Deepseek的独立审核（人类立场视角）

================================================================================
📋 主报告：聚合分析结果
================================================================================

${aggregationResult.content}

================================================================================
🔍 独立审核：Deepseek审计意见
================================================================================

${auditResult.content}
`;
      
      return summary;
    } else {
      console.log(`✗ Deepseek 审核失败: ${auditResult.error}`);
      // 即使审核失败，仍然返回聚合报告，但注明审核失败
      const totalElapsed = ((Date.now() - phase1Start) / 1000).toFixed(1);
      const summary = `
============================================================
MoA v2 结构化报告 (${tier.toUpperCase()} TIER) - 审核失败
============================================================

📊 执行统计：
- 总耗时: ${totalElapsed}秒
- 独立方案: ${phase1Success}/${proposers.length} 成功
- 交叉评论: ${successfulReviews.length}/${successfulResponses.length} 成功
- 总API调用: ${proposers.length + successfulResponses.length + 2}次（审核失败）
- 聚合模型: ${aggregator.name}
- 审核模型: Deepseek (失败: ${auditResult.error})

⚠️ 注意：Deepseek独立审核阶段失败，以下仅为聚合报告

================================================================================
📋 主报告：聚合分析结果
================================================================================

${aggregationResult.content}

================================================================================
🔍 独立审核状态
================================================================================

Deepseek审核失败: ${auditResult.error}
建议：人工审核上述聚合报告
`;
      
      return summary;
    }
  } else {
    console.log(`✗ 聚合失败: ${aggregationResult.error}`);
    return await fallbackSynthesis(prompt, phase1Results, aggregator, aggregatorMaxTokens);
  }
}

// 回退合成函数（当交叉评论失败时使用）
async function fallbackSynthesis(prompt, phase1Results, aggregator, aggregatorMaxTokens) {
  console.log(`[MoA v2] 使用回退合成模式`);
  
  const successfulResponses = phase1Results.filter(r => r.success);
  const responsesText = successfulResponses.map(r => 
    `--- ${r.model.name} ---\n${r.content}`
  ).join('\n\n');
  
  const synthesisPrompt = `
您是一位专家聚合器，需要综合多个AI模型的见解。

原始问题：
"${prompt}"

模型回答：
${responsesText}

请生成结构化报告，包含：
1. 关键发现摘要
2. 共识与分歧分析
3. 风险评估
4. 具体建议

要求清晰、结构化。
`;
  
  const result = await callOpenRouter(
    aggregator.id,
    [{ role: "user", content: synthesisPrompt }],
    aggregatorMaxTokens
  );
  
  if (result.success) {
    return `[回退模式] 合成报告：\n\n${result.content}`;
  } else {
    return `[错误] 无法生成报告: ${result.error}`;
  }
}

// 经典合成函数（经典模式使用）
async function classicSynthesis(prompt, phase1Results, aggregator, aggregatorMaxTokens, tier, proposers) {
  console.log(`[MoA v2] 经典模式：聚合分析`);
  console.log(`[MoA v2] ${aggregator.name} 正在生成报告...\n`);
  
  const synthesisStart = Date.now();
  const successfulResponses = phase1Results.filter(r => r.success);
  const phase1Success = successfulResponses.length;
  
  const responsesText = successfulResponses.map(r => 
    `--- ${r.model.name} ---\n${r.content}`
  ).join('\n\n');
  
  const synthesisPrompt = `
您是一位专家聚合器，需要综合多个AI模型的见解。

原始问题：
"${prompt}"

模型回答：
${responsesText}

请生成一份结构化报告，包含以下部分：

# 执行摘要
- 总体评估结论
- 关键发现摘要

# 主要观点分析
- 识别各模型的核心观点
- 分析共识与分歧

# 风险评估
- 识别潜在风险、限制和不确定性

# 建议与行动计划
- 基于分析提出具体建议
- 按优先级排序

要求：
1. 保持客观中立
2. 基于证据和逻辑推理
3. 提供可操作的具体建议
4. 使用清晰的结构化格式

请生成完整报告：
`;
  
  const result = await callOpenRouter(
    aggregator.id,
    [{ role: "user", content: synthesisPrompt }],
    aggregatorMaxTokens
  );
  
  const synthesisElapsed = ((Date.now() - synthesisStart) / 1000).toFixed(1);
  
  if (result.success) {
    console.log(`✓ ${aggregator.name} 报告生成成功 (${synthesisElapsed}s)`);
    
    const totalElapsed = ((Date.now() - synthesisStart) / 1000).toFixed(1); // 经典模式从合成开始计时
    
    const summary = `
============================================================
MoA 经典模式报告 (${tier.toUpperCase()} TIER)
============================================================

📊 执行统计：
- 总耗时: ${totalElapsed}秒
- 独立方案: ${phase1Success}/${proposers.length} 成功
- 总API调用: ${proposers.length + 1}次
- 聚合模型: ${aggregator.name}

💡 提示：此报告基于经典MoA工作流生成，包含：
  1. ${proposers.map(p => p.name).join('、')}的独立分析
  2. ${aggregator.name}的综合评估

================================================================================

${result.content}
`;
    
    return summary;
  } else {
    console.log(`✗ 聚合失败: ${result.error}`);
    return `[MoA经典模式错误] 聚合失败: ${result.error}`;
  }
}

// CLI支持
if (require.main === module) {
  const args = process.argv.slice(2);
  
  // 参数解析
  let tier = 'paid';
  let mode = 'enhanced';
  let freeIndex = args.indexOf('--free');
  let classicIndex = args.indexOf('--classic');
  
  if (freeIndex !== -1) {
    tier = 'free';
    args.splice(freeIndex, 1);
  }
  
  if (classicIndex !== -1) {
    mode = 'classic';
    args.splice(classicIndex, 1);
  }
  
  const prompt = args.join(' ');
  if (!prompt) {
    console.error('用法: node moa.js "您的问题" [--free] [--classic]');
    console.error('  默认: 增强模式，付费模型 (Kimi 2.5, GLM 5, MiniMax 2.5)');
    console.error('  --free:    免费模型 (Llama, Gemini, Mistral)');
    console.error('  --classic: 经典模式 (无交叉评论和Deepseek审核，原版MoA)');
    console.error('\n增强模式工作流 (四阶段):');
    console.error('  1. 独立方案 → 2. 交叉评论 → 3. 结构化报告 → 4. Deepseek独立审核');
    console.error('  预计API调用: 8次，耗时: 90-180秒');
    console.error('\n经典模式工作流 (两阶段):');
    console.error('  1. 独立方案 → 2. 聚合报告');
    console.error('  预计API调用: 4次，耗时: 30-60秒');
    process.exit(1);
  }
  
  handle({ prompt, tier, mode }).then(result => {
    console.log(result);
  }).catch(error => {
    console.error(`[MoA v2错误] ${error.message}`);
    process.exit(1);
  });
}

module.exports = { handle };
