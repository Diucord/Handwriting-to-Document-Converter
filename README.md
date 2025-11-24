# Handwriting to Document Converter

---

## Project Overview

**Handwriting to Document Converter** is a web application that takes **handwritten images** uploaded by users, processes them through the **Gemini API**, and converts them into clean, structured **HTML documents**. It then applies **KaTeX rendering** to display mathematical expressions and finally generates a **PDF file**.

With a mobile-friendly user interface (UI), users can easily convert handwritten notes or memos on paper into digital documents anytime, anywhere.

**Core Technologies:** **Gemini 2.5 Flash** (image analysis and HTML reconstruction), **Node.js** (backend), **React** (frontend), **Puppeteer** (HTML to PDF & KaTeX rendering)

---

## Key Features

* **Image Upload & Conversion:** Upload multiple handwritten images via camera, gallery, or file selection to convert them into structured documents.  
* **Gemini-based Document Reconstruction:** Analyzes handwritten content and rebuilds it into logical, structured HTML with titles, lists, and paragraphs.  
* **Automatic Math Rendering:** Detects math expressions ($$block$$ or $inline$) within the HTML and renders them beautifully using **KaTeX**.  
* **PDF File Generation:** Uses Puppeteer to convert the final HTML document into a fixed-layout A4-size PDF file.  
* **Conversion History Management:** Displays a simple record of the documents the user has converted.  
* **Mobile-Optimized UI:** Designed for an excellent experience on mobile devices.  

---

## Tech Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **AI/Core** | `@google/genai` (Gemini 2.5 Flash) | Analyzes handwritten images and reconstructs them into HTML documents |
| **Backend** | `Node.js`, `Express` | API server and file upload handling |
| **PDF/Rendering** | `Puppeteer`, `KaTeX` | Handles HTML to PDF conversion and math rendering |
| **Frontend** | `React`, `TypeScript` | Implements a mobile-optimized UI |
| **Package Management** | `npm` | Dependency and script management |

---

## Project Structure

```bash
├── client/           # Frontend (React)
├── server/           # Backend (Express + Gemini API)
│   ├── uploads/      # Uploaded images
│   ├── converted/    # Generated HTML/PDF files
│   └── index.js      # Core logic
├── Dockerfile        # Container setup
├── gcloud/           # Deployment configuration
└── README.md
```

---

## Installation & Execution

#### 1. Environment Setup

1.  **Install Node.js:** Make sure the latest version of Node.js is installed.
2.  **Set Up API Key:** Obtain a Gemini API Key from Google AI Studio or Google Cloud.
3.  **Create a .env file:** In the project root directory, create a .env file and add your API key.

    ```bash
    # .env file content
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    PORT=4000
    ```

#### 2. Install Dependencies & Run

Run the following commands in the project root directory:

```bash
# Install dependencies
npm install

# Run server in development mode
# 'npm run dev' starts the server with nodemon for automatic reload on file changes
npm run dev

# (or in production mode)
# npm start
```
Once the server starts successfully, you’ll see the following in your terminal:

```bash
✔ Puppeteer ready.
🚀 Server running at [http://0.0.0.0:4000](http://0.0.0.0:4000)
```

---

**Backend Core Code Overview**

#### 1. Document Conversion Endpoint (index.js)

The /api/convert-images endpoint performs the following steps:

1.  **Collect Images:** Uses multer to temporarily store uploaded files and prepare a GenerativePart array for Gemini API.
2.  **Call Gemini:** Sends the images along with a detailed reconstruction prompt to the gemini-2.5-flash model for HTML generation.
3.  **Generate PDF with Puppeteer:** Runs Puppeteer, injects the AI-generated HTML into a KaTeX-enabled template, and outputs the final PDF file.

#### 2. HTML Structure Enhancement (enhanceDocumentStructure)

Performs **regex-based post-processing** on the raw AI-generated HTML to improve readability and ensure consistent structure.

---

## Frontend Core Code Overview

#### 1. App State Management (`App.tsx`)

`App.tsx` manages the **three main stages** of the application (`start`, `convert`, `done`) and handles transitions between them.

#### 2. Download Handling (`DownloadPage.tsx`)

When the **Download PDF** button is clicked, the server-provided `pdfUrl` is used to dynamically create an `<a>` tag, trigger a `click()` event, and start the download.

---

## Contribution

Contributions for bug fixes or feature improvements are always welcome!  
Feel free to open an [Issue] or [Pull Request] to participate.

---

## Author 

Seyoon Oh  
Korea University — School of Industrial & Management Engineering  
Email: [osy7336@korea.ac.kr](mailto:osy7336@korea.ac.kr)
