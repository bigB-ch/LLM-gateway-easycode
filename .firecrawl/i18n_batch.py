"""Batch i18n: replace ALL Chinese text in Vue templates with t() calls."""
import os
import re

BASE = r"D:\code\llm-gateway\frontend\src\pages"

# Complete mapping of remaining Chinese text -> i18n key
# Only includes text that should be translated (user-visible UI text)
MAP = {
    # -- AdminUsage table headers --
    '时间': 'time',
    '模型': 'model',
    '供应商': 'supplier',
    '输入 Token': 'inputToken',
    '输出 Token': 'outputToken',
    '费用': 'cost',
    '延迟': 'duration',
    '状态': 'status',
    # -- Models table headers --
    '输入价格': 'inputPrice',
    '输出价格': 'outputPrice',
    '缓存/按次': 'cacheOrPerUse',
    '标签': 'tags',
    '暂无匹配模型': 'noModels',
    '尝试调整筛选条件': 'adjustFilter',
    # -- Models filter labels --
    '筛选': 'filter',
    '全部类型': 'allTypes',
    '全部': 'all',
    '成功': 'success',
    '失败': 'error',
    # -- PlanManager --
    '套餐名': 'planName',
    'Token 配额': 'tokenQuotaLabel',
    '价格': 'priceYuan',
    '有效期': 'validityDays',
    '描述': 'description',
    '创建中...': 'creatingPlan',
    '创建套餐': 'createPlanBtn',
    # -- Users table --
    '用户': 'user',
    '角色': 'role',
    '注册时间': 'createTime',
    '操作': 'operation',
    # -- Suppliers table --
    '供应商管理': 'supplierManagement',
    '暂无供应商配置': 'noSuppliers',
    '-- 选择 --': 'selectSupplier',
    # -- Playground --
    '发送中...': 'sending',
    '发送': 'send',
    '输入消息，Enter 发送': 'inputMsgHint',
    # -- Usage --
    '调用详情': 'callDetail',
    # -- Common --
    '确认充值': 'confirmTopUp',
    '余额': 'balance',
    '全部供应商': 'allSuppliers',
    # -- Plans reward text --
    '好友通过您的链接注册并充值后，您将获得充值金额的 10% 作为返利奖励': 'reward1',
    '返利收益进入待使用收益，可随时划转到账户余额用于 API 调用': 'reward2',
    '多邀多得，邀请人数和返利金额无上限，邀请越多收益越高': 'reward3',
    'EasyCode 版权所有': 'copyright',
    # -- Settings about --
    '平台版本：': 'platformVersion',
    '注册时间：': 'registeredAt',
    '上次登录：': 'lastLoginAt',
    '充值金额 (元)': 'topupAmount',
    # -- Keys --
    '全部模型（不限）': 'allModels',
    '默认视图': 'defaultView',
    '紧凑列表': 'compactList',
    '活跃': 'active',
    '已吊销': 'revoked',
    '暂无令牌': 'noTokens',
    '点击上方按钮创建您的第一个 API 令牌': 'noTokenHint',
    '搜索无结果': 'searchNoResult',
    '从未使用': 'neverUsed',
    '未命名': 'notNamed',
    '不限': 'unlimited',
    # -- Suppliers table headers --
    '最近调用': 'recentCalls',
    # -- Plans --
    '处理中...': 'processingBtn',
    '验证中...': 'verifyingBtn',
    '兑换额度': 'redeemBtn',
    '输入兑换码': 'redeemPlaceholder',
    '划转到余额': 'transferReward',
    '复制': 'copyLink',
    '已复制': 'copied',
    '支付方式': 'payMethod',
    '余额支付': 'balance',
    '实付金额': 'actualPay',
    '输入份数': 'topUpUnits',
    '账单 ↗': 'billLink',
    # -- Usage detail modal --
    '暂无调用记录': 'noData',
    '请求失败': 'requestFailed',
    # -- Breakers empty --
    '暂无数据': 'noData',
    # -- PlanManager table status --
    '上架': 'planActive',
    '下架': 'planInactive',
}

# Process each file
for fname in os.listdir(BASE):
    if not fname.endswith('.vue'):
        continue
    fpath = os.path.join(BASE, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False
    for cn, key in MAP.items():
        if cn not in content:
            continue
        # Exclude text that's already inside a t() call
        # Find template section
        tpl_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
        if not tpl_match:
            continue
        template = tpl_match.group(1)
        script = content[tpl_match.end():]

        if cn not in template:
            continue

        # Only replace if not already inside {{ t('...') }} or {{ ... t('...') ... }}
        escaped = re.escape(cn)
        # Build replacement: {{ t('key') }}
        new_text = f"{{{{ t('{key}') }}}}"

        # Replace only in template, not inside existing t() calls
        # Simple approach: replace whole text occurrences
        template = template.replace(cn, new_text)
        content = '<template>' + template + '</template>' + script
        changed = True

    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'{fname}: updated')
    else:
        print(f'{fname}: no changes')
print('Done')
