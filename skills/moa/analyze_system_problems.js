#!/usr/bin/env node

const { handle } = require('./scripts/moa.js');
const fs = require('fs');
const path = require('path');

async function main() {
    try {
        console.log('🚀 MoA系统问题综合分析启动...');
        console.log('📋 验证环境变量...');
        
        // 检查环境变量
        if (!process.env.OPENROUTER_API_KEY) {
            console.error('❌ OPENROUTER_API_KEY环境变量未设置');
            console.error('请在当前shell中设置: export OPENROUTER_API_KEY="your-key"');
            process.exit(1);
        }
        
        console.log(`✅ API密钥验证通过 (长度: ${process.env.OPENROUTER_API_KEY.length})`);
        
        // 读取问题描述
        const problemFile = path.join(__dirname, 'analysis_requests', 'all_system_problems.md');
        console.log(`📄 读取问题文件: ${problemFile}`);
        
        const prompt = fs.readFileSync(problemFile, 'utf-8');
        console.log(`📊 问题描述长度: ${prompt.length} 字符`);
        
        console.log('🧠 启动MoA深度分析 (付费层，预计45-90秒)...');
        console.log('⚠️ 注意: 此分析将调用4个AI模型，成本约$0.03');
        
        // 执行MoA分析
        const startTime = Date.now();
        const synthesis = await handle({
            prompt: prompt,
            tier: 'paid',
            mode: 'enhanced'
        });
        
        const elapsedTime = (Date.now() - startTime) / 1000;
        console.log(`✅ MoA分析完成 (耗时: ${elapsedTime.toFixed(1)}秒)`);
        
        // 保存结果
        const outputDir = path.join(__dirname, 'analysis_results');
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        const outputFile = path.join(outputDir, 'system_problems_moa_report.md');
        fs.writeFileSync(outputFile, synthesis, 'utf-8');
        
        console.log(`📝 分析报告已保存到: ${outputFile}`);
        console.log(`📊 报告长度: ${synthesis.length} 字符`);
        
        // 输出摘要
        console.log('\n📋 MoA分析报告摘要:');
        console.log('=' .repeat(60));
        
        // 提取报告关键部分
        const lines = synthesis.split('\n');
        let inSummary = false;
        let summaryLines = [];
        
        for (let i = 0; i < Math.min(lines.length, 30); i++) {
            const line = lines[i];
            if (line.includes('#') || line.includes('执行摘要') || line.includes('关键建议')) {
                inSummary = true;
            }
            if (inSummary && line.trim()) {
                summaryLines.push(line);
                if (summaryLines.length > 15) break;
            }
        }
        
        if (summaryLines.length > 0) {
            summaryLines.forEach(line => console.log(line));
        } else {
            // 如果没有找到摘要，显示前20行
            lines.slice(0, 20).forEach(line => {
                if (line.trim()) console.log(line);
            });
        }
        
        if (synthesis.length > 5000) {
            console.log('... (完整报告已保存到文件)');
        }
        
        console.log('=' .repeat(60));
        
        // 通知用户
        console.log('\n🎯 下一步:');
        console.log('1. 查看完整报告: ', outputFile);
        console.log('2. 根据MoA建议制定修复路线图');
        console.log('3. 按优先级实施系统修复');
        
    } catch (error) {
        console.error('❌ MoA分析失败:', error.message);
        console.error('堆栈:', error.stack);
        process.exit(1);
    }
}

// 执行
if (require.main === module) {
    main();
}

module.exports = { main };