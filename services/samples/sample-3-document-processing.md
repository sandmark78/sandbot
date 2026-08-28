# 样本任务3：文档处理

**任务类型**: PDF信息提取 + 结构化  
**输入数据**: 1份发票PDF（模拟）  
**输出**: JSON结构化数据

---

## 输入数据（模拟PDF内容）

```
INVOICE

Invoice Number: INV-2026-08-28-001
Date of Issue: August 28, 2026
Due Date: September 27, 2026

Bill To:
Acme Corporation
123 Business Ave, Suite 456
San Francisco, CA 94105
contact@acme.com

From:
Sandbot Data Services
456 AI Street
Beijing, China 100000
service@sandbot.ai

Description                          Qty    Unit Price    Amount
-----------------------------------------------------------------
Data Annotation Service              500    $0.03         $15.00
Content Moderation (1000 items)      1      $8.00         $8.00
Document Processing (50 docs)        1      $12.00        $12.00
Translation (5000 words)             1      $25.00        $25.00

                                          Subtotal:      $60.00
                                          Tax (0%):      $0.00
                                          Total:         $60.00

Payment Method: Bank Transfer
Bank: China Merchants Bank
Account: 6225 **** **** 1234
Account Name: Sandbot Data Services

Terms and Conditions:
1. Payment is due within 30 days of invoice date.
2. Late payments are subject to a 1.5% monthly interest charge.
3. All services are non-refundable once delivered.

Thank you for your business!
```

---

## 输出结果（JSON）

```json
{
  "invoice": {
    "invoice_number": "INV-2026-08-28-001",
    "date_of_issue": "2026-08-28",
    "due_date": "2026-09-27",
    "currency": "USD"
  },
  "bill_to": {
    "company": "Acme Corporation",
    "address": {
      "street": "123 Business Ave, Suite 456",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94105",
      "country": "USA"
    },
    "email": "contact@acme.com"
  },
  "from": {
    "company": "Sandbot Data Services",
    "address": {
      "street": "456 AI Street",
      "city": "Beijing",
      "zip": "100000",
      "country": "China"
    },
    "email": "service@sandbot.ai"
  },
  "line_items": [
    {
      "description": "Data Annotation Service",
      "quantity": 500,
      "unit_price": 0.03,
      "amount": 15.00
    },
    {
      "description": "Content Moderation (1000 items)",
      "quantity": 1,
      "unit_price": 8.00,
      "amount": 8.00
    },
    {
      "description": "Document Processing (50 docs)",
      "quantity": 1,
      "unit_price": 12.00,
      "amount": 12.00
    },
    {
      "description": "Translation (5000 words)",
      "quantity": 1,
      "unit_price": 25.00,
      "amount": 25.00
    }
  ],
  "totals": {
    "subtotal": 60.00,
    "tax_rate": 0,
    "tax_amount": 0.00,
    "total": 60.00
  },
  "payment": {
    "method": "Bank Transfer",
    "bank": "China Merchants Bank",
    "account_number_masked": "6225 **** **** 1234",
    "account_name": "Sandbot Data Services"
  },
  "terms": [
    "Payment is due within 30 days of invoice date.",
    "Late payments are subject to a 1.5% monthly interest charge.",
    "All services are non-refundable once delivered."
  ]
}
```

---

## 质量指标

- **准确率**: 100%（所有字段正确提取）
- **完整率**: 100%（无遗漏字段）
- **处理时间**: 1分钟（1份发票）
- **吞吐量**: 60份/小时

---

## 备注

- 自动识别发票结构（表头、账单方、服务方、明细、总计、付款信息、条款）
- 金额字段自动转换为数字类型
- 日期字段自动转换为ISO格式
- 地址字段自动拆分为结构化格式
- 账号自动脱敏（保留前后4位）

---

**任务完成时间**: 2026-08-28 11:07 UTC  
**实际耗时**: 1分钟  
**成本**: $0.50（1份 × $0.50/份）
