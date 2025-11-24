import { useState } from "react";
import StartPage from "./StartPage";
import ConversionPage from "./ConversionPage";
import DownloadPage from "./DownloadPage";

const SERVER_BASE_URL = import.meta.env.VITE_SERVER_URL;

export default function App() {
  const [step, setStep] = useState<"start" | "convert" | "done">("start");
  const [images, setImages] = useState<File[]>([]);
  const [pdfUrl, setPdfUrl] = useState<string>("");

  const handleImagesSelect = async (files: File[]) => {
    setImages(files);
    setStep("convert");

    const form = new FormData();
    files.forEach((file) => form.append("images", file));

    try {
        const res = await fetch(`${SERVER_BASE_URL}/api/convert-images`, {
            method: "POST",
            body: form,
        });

        if (!res.ok) {
            let errorMessage = `서버 오류 (${res.status} ${res.statusText})`;
            try {
                const errorData = await res.json();
                errorMessage += `: ${errorData.error || "알 수 없는 응답"}`;
            } catch {
                errorMessage += ": 응답 본문을 읽을 수 없습니다.";
            }
            throw new Error(errorMessage);
        }

        const data = await res.json();        
        const absolutePdfUrl = SERVER_BASE_URL + data.pdfUrl; 
        setPdfUrl(absolutePdfUrl);
        setStep("done");

    } catch (error) {
        console.error("Conversion failed:", error);
        alert(`❌ 문서 변환 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
        setStep("start"); 
    }
  };

  const handleFinish = () => {
    setImages([]);
    setPdfUrl("");
    setStep("start");
  };

  return (
    <div className="h-screen">
      {step === "start" && <StartPage onImagesSelect={handleImagesSelect} />}
      {step === "convert" && <ConversionPage images={images} />}
      {step === "done" && (
        <DownloadPage pdfUrl={pdfUrl} onFinish={handleFinish} />
      )}
    </div>
  );
}