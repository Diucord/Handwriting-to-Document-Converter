/**
 * render.js — Puppeteer 렌더링 스크립트.
 *
 * 사용법:
 *   PNG:  node render.js <input.html> <output.png>
 *   PDF:  node render.js <input.html> <output.pdf> --pdf
 *
 * puppeteer_runner.py에서 subprocess로 호출됨.
 */

const puppeteer = require('puppeteer');
const path = require('path');

const [, , inputPath, outputPath, mode] = process.argv;

if (!inputPath || !outputPath) {
  console.error('Usage: node render.js <input.html> <output.png|pdf> [--pdf]');
  process.exit(1);
}

// Windows 백슬래시를 슬래시로 변환해 file:// URL 구성
const absInput = path.resolve(inputPath);
const fileUrl = 'file:///' + absInput.replace(/\\/g, '/');

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();

    // 뷰포트: A4 기준 96dpi → 794×1123px
    await page.setViewport({ width: 794, height: 1123 });

    await page.goto(fileUrl, {
      waitUntil: 'networkidle0',
      timeout: 30000,
    });

    // CDN 라이브러리(Mermaid, KaTeX, Chart.js)가 networkidle0 이후
    // DOM 처리를 마칠 시간을 확보
    await new Promise(resolve => setTimeout(resolve, 500));

    if (mode === '--pdf') {
      await page.pdf({
        path: outputPath,
        format: 'A4',
        printBackground: true,
        margin: { top: '20mm', right: '15mm', bottom: '20mm', left: '15mm' },
      });
    } else {
      await page.screenshot({
        path: outputPath,
        fullPage: true,
      });
    }
  } finally {
    await browser.close();
  }
})();
