import express from "express";
import multer from "multer";
import cors from "cors";
import fs from "fs";
import dotenv from "dotenv";
import path from "path";
import { GoogleGenAI } from "@google/genai";
import puppeteer from "puppeteer";

// ---------------------
// Puppeteer Singleton
// ---------------------
let browserInstance;

async function initPuppeteer() {
    browserInstance = await puppeteer.launch({
        headless: "new",
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
        protocolTimeout: 180000,
    });
    console.log("✔ Puppeteer ready.");
}

dotenv.config();

const app = express();
app.use(cors({
  origin: "*",
  methods: ["GET", "POST"],
  allowedHeaders: ["Content-Type"],
}));

app.use(express.json());

if (!fs.existsSync("uploads")) fs.mkdirSync("uploads");
if (!fs.existsSync("converted")) fs.mkdirSync("converted");

const upload = multer({ dest: "uploads/" });
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
function fileToGenerativePart(filePath, mimeType) {
    return {
        inlineData: {
            data: fs.readFileSync(filePath).toString("base64"),
            mimeType,
        },
    };
}

// Document Structure Enhancement Processor
function enhanceDocumentStructure(html) {
    let out = html;

    // 기본 정리
    out = out.replace(/\r/g, "").trim();
    out = out.replace(/<p>\s*<\/p>/g, "");
    out = out.replace(/<p>\s*(<svg[\s\S]*?<\/svg>)\s*<\/p>/gi, "$1");
    out = out.replace(/<p>\s*<svg/gi, "<svg");
    out = out.replace(/^```.*\n/, "");
    out = out.replace(/\n```$/, "");
    out = out.replace(/<\s*\/?\s*mjx[^>]*>/gi, "");
    out = out.replace(/(<br\s*\/?>\s*){2,}/g, "</p><p>");
    out = out.replace(/([\.!?])\s+(?=[A-Z가-힣0-9])/g, "$1</p><p>");
    out = out.replace(/<p>\s*<h/g, "<h");

    // 리스트 감지
    out = out.replace(/^- ([^\n]+)/gm, "<ul><li>$1</li></ul>");
    out = out.replace(/^(\d{1,2}\.\s+.+)$/gm, "<h3>$1</h3>");
    out = out.replace(/^(\d{1,2}[-\.]\d{1,2}\.\s+.+)$/gm, "<h4>$1</h4>");
    out = out.replace(/^\(\d+\)\s+(.+)$/gm, "<h4>($1)</h4>");

    // 라인 분리
    let lines = out.split(/\n+/).map(l => l.trim()).filter(Boolean);
    let processed = [];
    let svgBuffer = [];
    let collectingSVG = false;
    const svgElementRegex =
        /^<(line|rect|path|circle|polyline|polygon|ellipse|text)\b[^>]*\/?>$/i;

    for (let line of lines) {
        if (svgElementRegex.test(line)) {
            collectingSVG = true;
            svgBuffer.push(line);
            continue;
        }

        if (collectingSVG && !svgElementRegex.test(line)) {
            processed.push(
                `<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">\n` +
                svgBuffer.join("\n") +
                `\n</svg>`
            );
            svgBuffer = [];
            collectingSVG = false;
        }

        if (line.includes("<img")) {
            processed.push(line);
            continue;
        }

        if (
            /^<h[1-6]>/.test(line) ||
            /^<svg/.test(line) ||
            /^<table/.test(line) ||
            /^<ul/.test(line) ||
            /^<li/.test(line)
        ) {
            processed.push(line);
        } else {
            processed.push(`<p>${line}</p>`);
        }
    }

    if (svgBuffer.length > 0) {
        processed.push(
            `<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">\n` +
            svgBuffer.join("\n") +
            `\n</svg>`
        );
    }

    let final = processed.join("\n").trim();

    return final.trim();
}

// Image → HTML → PDF Conversion
app.post("/api/convert-images", upload.array("images", 10), async (req, res) => {
    console.log("/api/convert-images called");

    let filesToClean = [];
    let page;

    try {
        if (!req.files || req.files.length === 0) {
            return res.status(400).json({ error: "No files uploaded." });
        }

        filesToClean = req.files;
        const imageParts = req.files.map((file) =>
            fileToGenerativePart(file.path, file.mimetype)
        );

const prompt = `
You are a document reconstruction engine.
Your task is to convert handwritten or unstructured notes into a clean, readable HTML document.

### Goal
Rebuild all the content as a single continuous HTML document.
Preserve the original flow, hierarchy, and relationships between ideas — whether the notes are scientific, creative, academic, business, or personal.

### Structure Rules
1. **Headings**
   - Use <h1> for the main title or top section.
   - Use <h2>, <h3> for subsections or important topics.

2. **Lists**
   - Convert bullets (•, -, ⚫), numbers, or dashes into <ul><li> or <ol><li>.
   - Preserve nested structures.

3. **Paragraphs**
   - Combine related lines into <p> blocks for readability.
   - Avoid breaking short related lines unnecessarily.

4. **Tables or Structured Data**
   - If the notes represent comparisons, attributes, or categories, use <table> with <tr><td>.

5. **Visuals or Diagrams**
   - Do NOT draw images or diagrams.
   - Instead, describe their contents textually and clearly using lists or tables.

6. **Output**
   - Return only the HTML body content (no <html>, <head>, or <body> tags).
   - The result must be a continuous, logically organized HTML document.
`;


        const aiResponse = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: [{ role: "user", parts: [...imageParts, { text: prompt }] }],
        });

        let html = aiResponse.text || "";
        if (!html.trim()) throw new Error("Empty HTML from AI");

        // 문서 구조 강화
        html = enhanceDocumentStructure(html);
        const filename = Date.now();
        const htmlPath = path.join("converted", `${filename}.html`);
        const pdfPath = path.join("converted", `${filename}.pdf`);
        fs.writeFileSync(htmlPath, html, "utf8");

        // Puppeteer HTML → PDF with KaTeX
        page = await browserInstance.newPage();
        await page.setContent(`
            <html>
            <head>
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
                <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
                        onload="window.katexLoaded = true;"></script>

                <style>
                    body {
                        font-family: "Inter", "Pretendard", sans-serif;
                        padding: 30px;
                        line-height: 1.6;
                        color: #222;
                    }
                    h1 { margin-top: 5x; margin-bottom: 20px; }
                    h2, h3 { margin-top: 10px; margin-bottom: 10px; }
                    h1 { font-size: 1.8rem; font-weight: 700; }
                    h2 { font-size: 1.5rem; font-weight: 600; }
                    h3 { font-size: 1.3rem; font-weight: 500; }

                    p { margin: 10px 0; font-size: 1rem; }
                    ul { padding-left: 20px; margin: 10px 0; }
                    li { margin-bottom: 10px; }

                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }
                    th, td {
                        border: 1px solid #ccc;
                        padding: 10px;
                    }

                    .katex { font-size: 1.15rem; }
                </style>
            </head>

            <body>
            ${html}

            <script>
                window.renderFinished = false;

                function renderMath() {
                    const body = document.body;

                    // $$ block math $$
                    body.innerHTML = body.innerHTML.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, (m, f) => {
                        try {
                            return "<div class='math-block'>" + katex.renderToString(f.trim(), { displayMode: true, throwOnError: false }) + "</div>";
                        } catch {
                            return m;
                        }
                    });

                    // $ inline math $
                    body.innerHTML = body.innerHTML.replace(/\\$(.+?)\\$/g, (m, f) => {
                        try {
                            return katex.renderToString(f.trim(), { displayMode: false, throwOnError: false });
                        } catch {
                            return m;
                        }
                    });

                    window.renderFinished = true;
                }

                // KaTeX 로드 대기 후, 최대 3초만 추가 대기 후 다음 단계로 진행
                let attempts = 0;
                const maxAttempts = 30; // 30 attempts * 80ms = 2.4초
                const checker = setInterval(() => {
                    if (window.katexLoaded) {
                        renderMath();
                        clearInterval(checker);
                    } else if (attempts >= maxAttempts) {
                        // KaTeX 로드에 실패하더라도 수식 없이 다음 단계로 진행
                        console.log("KaTeX failed to load, proceeding without math rendering.");
                        window.renderFinished = true;
                        clearInterval(checker);
                    }
                    attempts++;
                }, 80);
            </script>

            </body>
            </html>
            `,
            { waitUntil: "domcontentloaded" } 
        );

        // Puppeteer 대기 로직 (최대 60초)
        await page.waitForFunction(() => window.renderFinished === true, {
            timeout: 60000,
        });

        await page.pdf({
            path: pdfPath,
            format: "A4",
            printBackground: true,
        });

        return res.json({
            htmlUrl: "/converted/" + path.basename(htmlPath),
            pdfUrl: "/converted/" + path.basename(pdfPath),
        });
    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Conversion failed." });
    } finally {
        filesToClean.forEach((f) => {
            try {
                fs.unlinkSync(f.path);
            } catch {}
        });
        if (page) {
            await page.close().catch(() => {});
        }
    }
});

app.use("/converted", express.static("converted"));

initPuppeteer().then(() => {
    app.listen(process.env.PORT || 4000, "0.0.0.0", () =>
        console.log(`🚀 Server running at http://0.0.0.0:${process.env.PORT || 4000}`)
    );
});