import { useState } from "react";
import LandingPage from "./LandingPage";
import StartPage from "./StartPage";
import ConversionPage from "./ConversionPage";
import DownloadPage from "./DownloadPage";
import LoginPage from "./LoginPage";
import SignupPage from "./SignupPage";
import ForgotPasswordPage from "./ForgotPasswordPage";
import ProfilePage from "./ProfilePage";
import { useAuth } from "./useAuth";
import { apiFetch, apiGet, SERVER_BASE_URL } from "./api";

type Stage =
  | "landing"
  | "start"
  | "convert"
  | "done"
  | "login"
  | "signup"
  | "forgot-password"
  | "profile";

export interface SessionHistoryItem {
  id: number;
  title: string;
  file_type: string;
  file_url: string;
  created_at: string;
}

export default function App() {
  // 첫 화면은 랜딩. 체험하기를 누르면 로그인 없이 업로드 화면으로 갑니다.
  const [step, setStep] = useState<Stage>("landing");
  const [images, setImages] = useState<File[]>([]);
  const [pdfUrl, setPdfUrl] = useState<string>("");
  const [wordUrl, setWordUrl] = useState<string>("");
  const [exportFormat, setExportFormat] = useState<"pdf" | "word">("pdf");
  const [sessionHistory, setSessionHistory] = useState<SessionHistoryItem[]>([]);
  const [progress, setProgress] = useState<number>(0);
  const [progressMessage, setProgressMessage] = useState<string>("");
  // 파이프라인 단계 (extract·classify·render·assemble) — 변환 화면에서 표시
  const [stage, setStage] = useState<string>("");
  // 현재 단계의 세부 진행 (예: 3/8 페이지)
  const [stageDetail, setStageDetail] = useState<{ done: number; total: number } | null>(null);

  const { user, loading, login, logout, refreshUser, updateProfile, uploadProfileImage } = useAuth();

  const pollProgress = async (conversionId: string): Promise<{ pdfUrl: string; wordUrl: string }> => {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const res = await apiGet(`/api/convert-progress/${conversionId}`);
          if (!res.ok) {
            clearInterval(interval);
            reject(new Error("진행률 조회 실패"));
            return;
          }

          const data = await res.json();
          setProgress(data.percent || 0);
          setProgressMessage(data.message || "");
          if (data.stage) setStage(data.stage);
          setStageDetail(
            data.detail && data.detail.total ? data.detail : null
          );

          if (data.status === "done") {
            clearInterval(interval);
            // Save history
            await apiFetch(`/api/convert-complete/${conversionId}`, { method: "POST" });
            resolve({
              pdfUrl: data.pdfUrl ? SERVER_BASE_URL + data.pdfUrl : "",
              wordUrl: data.wordUrl ? SERVER_BASE_URL + data.wordUrl : "",
            });
          } else if (data.status === "error") {
            clearInterval(interval);
            reject(new Error(data.error || "변환 실패"));
          }
        } catch (err) {
          clearInterval(interval);
          reject(err);
        }
      }, 1000);
    });
  };

  const handleImagesSelect = async (files: File[], format: "pdf" | "word") => {
    setImages(files);
    setExportFormat(format);
    setProgress(0);
    setProgressMessage("변환 준비 중...");
    setStage("extract");
    setStageDetail(null);
    setStep("convert");

    const form = new FormData();
    files.forEach((file) => form.append("images", file));
    form.append("export_format", format);

    try {
      const res = await apiFetch("/api/convert-images", {
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

      const { conversionId } = await res.json();
      const result = await pollProgress(conversionId);

      setPdfUrl(result.pdfUrl);
      setWordUrl(result.wordUrl);

      const firstFilename = files[0]?.name || "변환 문서";
      const title = firstFilename.replace(/\.[^.]+$/, "").slice(0, 50);
      const fileUrl = format === "pdf" ? result.pdfUrl : result.wordUrl;
      if (fileUrl) {
        setSessionHistory((prev) => [
          {
            id: Date.now(),
            title,
            file_type: format === "pdf" ? "pdf" : "docx",
            file_url: fileUrl,
            created_at: new Date().toISOString(),
          },
          ...prev,
        ]);
      }

      setStep("done");
    } catch (error) {
      console.error("Conversion failed:", error);
      alert(`문서 변환 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
      setStep("start");
    }
  };

  const handleFinish = () => {
    setImages([]);
    setPdfUrl("");
    setWordUrl("");
    setProgress(0);
    setProgressMessage("");
    setStage("");
    setStageDetail(null);
    setStep("landing");
  };

  if (loading) {
    return null;
  }

  return (
    <div className="h-screen">
      {step === "landing" && (
        <LandingPage
          isLoggedIn={!!user}
          onStart={() => setStep("start")}
          onGoLogin={() => setStep(user ? "start" : "login")}
        />
      )}

      {step === "login" && (
        <LoginPage
          onLogin={async (email, pw) => {
            await login(email, pw);
            setStep("start");
          }}
          onGoSignup={() => setStep("signup")}
          onGoForgotPassword={() => setStep("forgot-password")}
          onBack={() => setStep("landing")}
        />
      )}

      {step === "signup" && (
        <SignupPage
          onSignupComplete={() => {
            refreshUser();
            setStep("start");
          }}
          onGoLogin={() => setStep("login")}
        />
      )}

      {step === "forgot-password" && (
        <ForgotPasswordPage onGoLogin={() => setStep("login")} />
      )}

      {step === "profile" && user && (
        <ProfilePage
          user={user}
          onBack={() => setStep("start")}
          onLogout={() => {
            logout();
            setStep("start");
          }}
          onUpdateProfile={updateProfile}
          onUploadProfileImage={uploadProfileImage}
        />
      )}

      {step === "start" && (
        <StartPage
          user={user}
          sessionHistory={sessionHistory}
          onImagesSelect={handleImagesSelect}
          onGoLogin={() => setStep("login")}
          onGoProfile={() => setStep("profile")}
          onGoHome={() => setStep("landing")}
        />
      )}

      {step === "convert" && (
        <ConversionPage
          images={images}
          progress={progress}
          progressMessage={progressMessage}
          stage={stage}
          stageDetail={stageDetail}
          onHome={handleFinish}
        />
      )}

      {step === "done" && (
        <DownloadPage
          images={images}
          pdfUrl={pdfUrl}
          wordUrl={wordUrl}
          exportFormat={exportFormat}
          onFinish={handleFinish}
          onBack={() => setStep("start")}
        />
      )}
    </div>
  );
}
