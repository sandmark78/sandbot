#!/usr/bin/env node
/**
 * 生成会员激活码
 * 
 * 用法:
 * node generate-code.js monthly    # 生成月度会员激活码
 * node generate-code.js yearly     # 生成年度会员激活码
 * node generate-code.js lifetime   # 生成永久会员激活码
 * node generate-code.js batch 10   # 批量生成10个月度会员激活码
 */

const crypto = require('crypto');

// 生成随机4字符
function randomChars() {
  return crypto.randomBytes(2).toString('hex').toUpperCase().slice(0, 4);
}

// 生成激活码
function generateCode(plan) {
  const part1 = randomChars();
  const part2 = randomChars();
  const part3 = randomChars();
  return `SANDBOT-${part1}-${part2}-${part3}`;
}

// 主函数
function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('用法:');
    console.log('  node generate-code.js monthly    # 生成月度会员激活码');
    console.log('  node generate-code.js yearly     # 生成年度会员激活码');
    console.log('  node generate-code.js lifetime   # 生成永久会员激活码');
    console.log('  node generate-code.js batch 10   # 批量生成10个月度会员激活码');
    process.exit(1);
  }

  const command = args[0];
  
  if (command === 'batch') {
    const count = parseInt(args[1]) || 10;
    const plan = args[2] || 'monthly';
    
    console.log(`\n生成 ${count} 个 ${plan} 会员激活码:\n`);
    
    for (let i = 0; i < count; i++) {
      const code = generateCode(plan);
      console.log(code);
    }
    console.log('');
  } else if (['monthly', 'yearly', 'lifetime'].includes(command)) {
    const code = generateCode(command);
    console.log(`\n${command} 会员激活码:`);
    console.log(code);
    console.log('');
  } else {
    console.error(`未知命令: ${command}`);
    process.exit(1);
  }
}

main();
