// 加载核心逻辑
const { extractPantones, dedupe, getBase, dbLookup, convertOne } = require('./_core_logic.js');

let pass = 0, fail = 0;
const results = [];

function test(name, got, expected) {
  const ok = JSON.stringify(got) === JSON.stringify(expected);
  if (ok) pass++;
  else { fail++; results.push({ name, got, expected }); }
  const sym = ok ? 'PASS' : 'FAIL';
  process.stdout.write(sym + '  ' + name + '\n');
}
function testTrue(name, val) {
  test(name, !!val, true);
}
function testFalse(name, val) {
  test(name, !!val, false);
}

// ─── 1. extractPantones 正则 ───────────────────────────────────────
const ep = extractPantones;

test('提取-标准TPG', ep('19-4150TPG'), ['19-4150TPG']);
test('提取-标准TCX', ep('19-4150TCX'), ['19-4150TCX']);
test('提取-裸号', ep('19-4150'), ['19-4150']);
test('提取-空格分隔TPG', ep('19-0303 TPG'), ['19-0303TPG']);
test('提取-空格分隔TCX', ep('11-0602 TCX'), ['11-0602TCX']);
test('提取-逗号分隔', ep('19-4150TPG,18-1660TCX'), ['19-4150TPG','18-1660TCX']);
test('提取-混在文字中', ep('色号：19-4150TPG 蓝色 18-1660TCX 红色'), ['19-4150TPG','18-1660TCX']);
test('提取-每行一个', ep('19-4150TPG\n18-1660TCX\n15-1520TPG'), ['19-4150TPG','18-1660TCX','15-1520TPG']);
test('提取-制表符分隔', ep('19-4150TPG\t18-1660TCX'), ['19-4150TPG','18-1660TCX']);
test('提取-空字符串', ep(''), []);
test('提取-无色号文本', ep('hello world 123'), []);
test('提取-小写后缀', ep('19-4150tpg 18-1660tcx'), ['19-4150TPG','18-1660TCX']);
test('提取-多个裸号', ep('19-4150 18-1660 15-1520'), ['19-4150','18-1660','15-1520']);
test('提取-去掉<7字符', ep('1-234'), []);  // 不足7字符应被过滤

// ─── 2. dedupe ────────────────────────────────────────────────────
test('去重-大小写不敏感', dedupe(['19-4150TPG','19-4150tpg','18-1660TCX']), ['19-4150TPG','18-1660TCX']);
test('去重-保序', dedupe(['B','A','B','C']), ['B','A','C']);
test('去重-空数组', dedupe([]), []);

// ─── 3. getBase ───────────────────────────────────────────────────
test('getBase-TPG', getBase('19-4150TPG'), '19-4150');
test('getBase-TCX', getBase('19-4150TCX'), '19-4150');
test('getBase-裸号', getBase('19-4150'), '19-4150');
test('getBase-大写', getBase('19-4150TPG'), '19-4150');

// ─── 4. dbLookup ──────────────────────────────────────────────────
// 精确 TPG
const r1 = dbLookup('19-4150TPG');
testTrue('lookup-TPG精确', r1);
test('lookup-TPG-SKC', r1 && r1.s, '6648');
test('lookup-TPG-name', r1 && r1.n, 'Princess Blue');

// TCX fallback → 找到同 base 的 TPG
const r2 = dbLookup('19-4150TCX');
testTrue('lookup-TCX fallback', r2);
test('lookup-TCX-SKC同TPG', r2 && r2.s, '6648');

// 裸号 fallback
const r3 = dbLookup('19-4150');
testTrue('lookup-裸号 fallback', r3);
test('lookup-裸号-SKC', r3 && r3.s, '6648');

// 大小写不敏感
const r4 = dbLookup('19-4150tpg');
testTrue('lookup-小写TPG', r4);

// 带空格
const r5 = dbLookup('19-4150 TPG');
// trim 后再查
testTrue('lookup-带空格', r5);

// 不存在
const r6 = dbLookup('99-9999TPG');
test('lookup-不存在', r6, null);

// ─── 5. convertOne ────────────────────────────────────────────────
const c1 = convertOne('19-4150TPG', '');
test('convert-found', c1.found, true);
test('convert-SKC', c1.skc, '6648');
test('convert-tpg', c1.tpg, '19-4150TPG');
test('convert-tcx', c1.tcx, '19-4150TCX');
test('convert-target空', c1.target, '');

const c2 = convertOne('19-4150TPG', 'TCX');
test('convert-target-TCX', c2.target, '19-4150TCX');

const c3 = convertOne('19-4150TCX', 'TPG');
test('convert-TCX输入-target-TPG', c3.target, '19-4150TPG');
test('convert-TCX输入-found', c3.found, true);

const c4 = convertOne('99-9999TPG', 'TCX');
test('convert-不存在-found', c4.found, false);
test('convert-不存在-skc空', c4.skc, '');
test('convert-不存在-tpg推算', c4.tpg, '99-9999TPG');
test('convert-不存在-tcx推算', c4.tcx, '99-9999TCX');

const c5 = convertOne('19-4150', '');
test('convert-裸号-found', c5.found, true);
test('convert-裸号-tpg', c5.tpg, '19-4150TPG');

// ─── 6. 真实色号批量验证（来自 pptx 测试场景）────────────────────
const pptxCases = [
  { input: '19-0303TCX', skc: '9760' },
  { input: '11-0602TCX', skc: '0156' },
  { input: '18-0306TCX', skc: '9627' },
  { input: '19-1217TCX', skc: '8648' },
  { input: '18-1142TCX', skc: '8591' },
  { input: '16-1334TCX', skc: '8404' },
  { input: '15-1145TCX', skc: '2310' },
  { input: '19-1624TCX', skc: '3769' },
  { input: '19-4024TCX', skc: '6770' },
  { input: '17-1044TCX', skc: '8547' },
  { input: '11-4801TPG', skc: '0179' },
  { input: '19-1015TPG', skc: '8705' },
];
pptxCases.forEach(({ input, skc }) => {
  const r = convertOne(input, '');
  test('pptx-' + input + '-found', r.found, true);
  test('pptx-' + input + '-skc', r.skc, skc);
});

// ─── 7. extractPantones 对 OCR 典型输出的处理 ─────────────────────
const ocrText = `1 19-0303 TCX Matte Black 曜石黑
2 11-0602 TCX Off White 云雾白
3 18-0306 TCX Charcoal 岩炭灰
11 11-4801 TPG Tofu 云霜白
12 19-1015 TPG Bracken 醇咖棕`;
const ocrGot = extractPantones(ocrText);
test('OCR文本-提取数量', ocrGot.length, 5);
test('OCR文本-第1个', ocrGot[0], '19-0303TCX');
test('OCR文本-第3个', ocrGot[2], '18-0306TCX');
test('OCR文本-TPG', ocrGot[3], '11-4801TPG');

// ─── 8. 边界案例 ──────────────────────────────────────────────────
test('边界-全大写', extractPantones('19-4150TPG'), ['19-4150TPG']);
test('边界-全小写', extractPantones('19-4150tpg'), ['19-4150TPG']);
test('边界-混合大小写', extractPantones('19-4150Tpg'), ['19-4150TPG']);
// 多余空格
test('边界-多空格', extractPantones('19-4150  TPG'), ['19-4150TPG']);
// 连续多个相同
const dup2 = extractPantones('19-4150TPG 19-4150TPG 18-1660TCX');
// extractPantones 不去重，dedupe 去重
test('边界-重复提取(不去重)', dup2.length, 3);
test('边界-去重后', dedupe(dup2).length, 2);

// ─── 汇总 ────────────────────────────────────────────────────────
process.stdout.write('\n');
process.stdout.write('─'.repeat(50) + '\n');
process.stdout.write(`通过: ${pass}  失败: ${fail}  共: ${pass+fail}\n`);
if (results.length) {
  process.stdout.write('\n失败详情:\n');
  results.forEach(r => {
    process.stdout.write(`  ${r.name}\n`);
    process.stdout.write(`    期望: ${JSON.stringify(r.expected)}\n`);
    process.stdout.write(`    实得: ${JSON.stringify(r.got)}\n`);
  });
}
process.exit(fail > 0 ? 1 : 0);
