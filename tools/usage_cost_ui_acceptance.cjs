// Read-only browser acceptance against the local, built console.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

(async () => {
  const base = process.env.CONSOLE_URL || 'http://127.0.0.1:5051';
  const output = path.resolve(process.env.ACCEPTANCE_OUTPUT || 'workspace/usage_cost_20260916');
  const workspace = path.resolve(process.env.RESEARCH_WORKSPACE || 'workspace/finals_execution_20260915');
  const id = crypto.createHash('sha1').update(workspace).digest('hex').slice(0, 10);
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || chromium.executablePath(), headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--proxy-server=direct://', '--proxy-bypass-list=*'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('response', response => { if (response.status() >= 400 && response.url().startsWith(base)) errors.push(`${response.status()} ${response.url()}`); });
  try {
    const api = await page.request.get(`${base}/api/workspaces/${id}/costs`);
    assert.equal(api.status(), 200);
    const report = await api.json();
    const expected = `USD ${Number(report.summary.currencies.USD.total).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}`;
    const started = Date.now();
    await page.goto(`${base}/#/costs?research=${id}`, { waitUntil: 'domcontentloaded' });
    await page.getByTestId('cost-total').waitFor();
    assert.equal(await page.getByTestId('cost-total').innerText(), expected);
    const loadMs = Date.now() - started;
    for (const [tab, key] of [['单次研究', 'researches'], ['单个会话', 'sessions'], ['整轮任务', 'tasks']]) {
      await page.locator('.costs .n-tabs-tab').filter({ hasText: tab }).click();
      await page.waitForFunction(count => document.querySelector('.costs .scroll tbody')?.children.length === count, report[key].length);
    }
    for (const model of ['gpt-5.6-sol', 'gpt-5.6-luna', 'gpt-6-astra', 'deepseek-flash']) {
      await page.getByRole('textbox', { name: `${model} input`, exact: true }).waitFor();
    }
    await page.getByText('统计完整性与计价依据', { exact: true }).click();
    assert((await page.locator('.costs').innerText()).includes('缺少回执的失败会话'));
    await page.screenshot({ path: path.join(output, 'costs-desktop.png'), fullPage: true });
    const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: '导出 JSON' }).click()]);
    const downloaded = path.join(output, 'browser-export.json');
    await download.saveAs(downloaded);
    assert.deepEqual(JSON.parse(await fs.readFile(downloaded, 'utf8')).summary, report.summary);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/workspaces/${id}/costs`) && r.status() === 200),
      page.getByRole('button', { name: '刷新', exact: true }).click(),
    ]);
    assert.equal(await page.getByTestId('cost-total').innerText(), expected);
    // Exercise the workspace selector, including the larger all-research report.
    await page.locator('.costs .n-base-selection').first().click();
    // The menu virtualizes options and initially scrolls to the current study.
    await page.locator('.costs .n-base-selection-input').fill('全部');
    const [allResponse] = await Promise.all([
      page.waitForResponse(r => r.url().endsWith('/api/billing/summary') && r.status() === 200),
      page.getByText('全部研究与后续调用', { exact: true }).click(),
    ]);
    const allReport = await allResponse.json();
    const allExpected = `USD ${Number(allReport.summary.currencies.USD.total).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}`;
    await page.waitForFunction(total => document.querySelector('[data-testid="cost-total"]')?.textContent === total, allExpected);
    await page.setViewportSize({ width: 430, height: 932 });
    await page.waitForFunction(() => getComputedStyle(document.querySelector('.ctx-right')).display === 'none' && document.documentElement.scrollWidth <= 430);
    const mobileWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    assert(mobileWidth <= 430, `page overflows mobile viewport: ${mobileWidth}`);
    await page.screenshot({ path: path.join(output, 'costs-mobile.png'), fullPage: true });
    assert.deepEqual(errors, []);
    const result = { passed: true, url: `${base}/#/costs?research=${id}`, loadMs, displayedTotal: expected,
      usageRecords: report.summary.usage_records, missingUsage: report.summary.missing_usage,
      tabs: ['research', 'session', 'task'], modelInputs: 4, downloadMatches: true, allResearchTotal: allExpected,
      duplicatesIgnored: allReport.duplicates_ignored, mobileWidth, browserErrors: errors };
    await fs.writeFile(path.join(output, 'browser-acceptance.json'), JSON.stringify(result, null, 2) + '\n');
    process.stdout.write(JSON.stringify(result) + '\n');
  } catch (error) {
    await fs.writeFile(path.join(output, 'browser-failure.json'), JSON.stringify({ error: String(error), browserErrors: errors,
      text: await page.locator('body').innerText().catch(() => ''), tabs: await page.locator('[class*=tabs]').evaluateAll(nodes => nodes.slice(0, 20).map(n => ({ cls: n.className, text: n.textContent }))).catch(() => []) }, null, 2));
    await page.screenshot({ path: path.join(output, 'costs-failure.png'), fullPage: true }).catch(() => {});
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
