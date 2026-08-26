import { useEffect, useState } from "react";
import { FileText, Lock, Download, AlertCircle, Clock } from "lucide-react";
import Logo from "./Logo";
import { SERVER_BASE_URL } from "./api";
import styles from "./SharedPage.module.css";

interface SharedView {
  title: string;
  file_type: string;
  expires_at: string | null;
  requires_password: boolean;
  remaining_downloads: number | null;
  file_url: string | null;
}

interface Props {
  token: string;
  /** 서비스 홈으로 (로고·CTA) */
  onGoHome: () => void;
}

/**
 * 공유 링크로 들어온 사람이 보는 화면.
 *
 * 로그인하지 않은 사람이 여는 화면이라 앱 내부 상태에 기대지 않고
 * 토큰만으로 동작합니다.
 *
 * 다운로드는 두 단계입니다. 화면을 열 때는 GET 으로 정보만 받고,
 * 실제로 받을 때 POST access 를 불러 횟수를 올립니다. 열어보기만 해도
 * 한도가 깎이면 안 되기 때문입니다.
 */
export default function SharedPage({ token, onGoHome }: Props) {
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [error, setError] = useState("");
  const [info, setInfo] = useState<SharedView | null>(null);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch(`${SERVER_BASE_URL}/api/share/public/${token}`)
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || "링크를 열 수 없습니다.");
        }
        return res.json();
      })
      .then((data: SharedView) => {
        setInfo(data);
        setState("ok");
      })
      .catch((e: Error) => {
        setError(e.message);
        setState("error");
      });
  }, [token]);

  const startDownload = (fileUrl: string) => {
    const a = document.createElement("a");
    a.href = fileUrl.startsWith("http") ? fileUrl : `${SERVER_BASE_URL}${fileUrl}`;
    a.download = "";
    a.click();
  };

  const handleDownload = async () => {
    if (!info) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${SERVER_BASE_URL}/api/share/public/${token}/access`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: password || null }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "다운로드에 실패했습니다.");

      setInfo(body);
      if (body.file_url) startDownload(body.file_url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "다운로드에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={styles["page"]}>
      <header className={styles["bar"]}>
        <button className={styles["brand"]} onClick={onGoHome} aria-label="홈으로">
          <Logo size={26} />
        </button>
      </header>

      <main className={styles["main"]}>
        <div className={styles["card"]}>
          {state === "loading" && (
            <p className={styles["muted"]}>링크를 확인하고 있습니다…</p>
          )}

          {state === "error" && (
            <>
              <span className={`${styles["badge"]} ${styles["badgeBad"]}`}>
                <AlertCircle size={30} strokeWidth={2} />
              </span>
              <h1 className={styles["title"]}>링크를 열 수 없습니다</h1>
              <p className={styles["desc"]}>{error}</p>
              <button className={styles["ghost"]} onClick={onGoHome}>
                Notaformat 둘러보기
              </button>
            </>
          )}

          {state === "ok" && info && (
            <>
              <span className={styles["badge"]}>
                <FileText size={30} strokeWidth={2} />
              </span>

              <h1 className={styles["title"]}>{info.title}</h1>

              <div className={styles["metaRow"]}>
                <span className={styles["chip"]}>
                  {info.file_type.toUpperCase()}
                </span>
                {info.expires_at && (
                  <span className={styles["chip"]}>
                    <Clock size={12} strokeWidth={2.4} aria-hidden="true" />
                    {new Date(info.expires_at).toLocaleDateString("ko-KR")} 만료
                  </span>
                )}
                {info.remaining_downloads !== null && (
                  <span className={styles["chip"]}>
                    {info.remaining_downloads}회 남음
                  </span>
                )}
              </div>

              {info.requires_password && (
                <div className={styles["lockBox"]}>
                  <label className={styles["lockLabel"]} htmlFor="share-pw">
                    <Lock size={14} strokeWidth={2.4} aria-hidden="true" />
                    비밀번호가 설정된 문서입니다
                  </label>
                  <input
                    id="share-pw"
                    type="password"
                    className={styles["input"]}
                    value={password}
                    placeholder="비밀번호 입력"
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleDownload();
                    }}
                  />
                </div>
              )}

              {error && <p className={styles["err"]}>{error}</p>}

              <button
                className={styles["primary"]}
                onClick={handleDownload}
                disabled={busy || (info.requires_password && !password)}
              >
                <Download size={18} strokeWidth={2.3} aria-hidden="true" />
                {busy ? "받는 중…" : "다운로드"}
              </button>

              <button className={styles["ghost"]} onClick={onGoHome}>
                나도 손글씨 변환해보기
              </button>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
