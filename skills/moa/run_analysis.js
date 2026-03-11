#!/usr/bin/env node

const { handle } = require('./scripts/moa.js');
const fs = require('fs');
const path = require('path');

async function main() {
    try {
        console.log('🚀 MoA系统问题分析开始...');
        console.log('📋 读取问题描述文件...');
        
        // 读取问题描述
        const problemFile = path.join(__dirname, 'analysis_requests', 'all_system_problems.md');
        const prompt = fs.readFileSync(problemFile, 'utf-8');
        
        console.log(`📄 问题描述长度: ${prompt.length} 字符`);
        console.log('🧠 启动MoA分析（预计45-90秒）...');
        
        // 执行MoA分析
        const startTime = Date.now();
        const synthesis = await handle({
            prompt: prompt,
            tier: 'paid' // 使用付费层
        });
        
        const elapsedTime = (Date.now() - startTime) / 1000;
        console.log(`✅ MoA分析完成 (耗时: ${elapsedTime.toFixed(1)}秒)`);
        
        // 保存结果
        const outputDir = path.join(__dirname, 'analysis_results');
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        const outputFile = path.join(outputDir, 'all_system_problems_report.md');
        fs.writeFileSync(outputFile, synthesis, 'utf-8');
        
        console.log(`📝 分析报告已保存到: ${outputFile}`);
        console.log(`📊 报告长度: ${synthesis.length} 字符`);
        
        // 输出摘要
        console.log('\n📋 报告摘要:');
        console.log('=' .repeat(60));
        
        // 提取前几行作为摘要
        const lines = synthesis.split('\n').slice(0, 20);
        lines.forEach(line => {
            if (line.trim()) console.log(line);
        });
        
        if (synthesis.length > 5000) {
            console.log('... (完整报告已保存到文件)');
        }
        
        console.log('=' .repeat(60));
        
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