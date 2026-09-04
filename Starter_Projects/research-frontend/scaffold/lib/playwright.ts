import { chromium, type Browser, type Page } from "playwright";

let browser: Browser | null = null;
let currentPage: Page | null = null;

export async function getPage(): Promise<Page> {
  if (!browser) browser = await chromium.launch({ headless: true });
  if (!currentPage || currentPage.isClosed()) currentPage = await browser.newPage();
  return currentPage;
}

export async function navigate(url: string): Promise<string> {
  const page = await getPage();
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 15000 });
  await page.waitForTimeout(500);
  return (await page.evaluate(() => document.body.innerText)).slice(0, 8000);
}

export async function clickByText(text: string): Promise<string> {
  const page = await getPage();
  await page.getByText(text, { exact: false }).first().click({ timeout: 5000 });
  await page.waitForTimeout(500);
  return (await page.evaluate(() => document.body.innerText)).slice(0, 8000);
}

export async function screenshot(): Promise<string> {
  const page = await getPage();
  const buf = await page.screenshot({ type: "png", fullPage: false });
  return `data:image/png;base64,${buf.toString("base64")}`;
}
