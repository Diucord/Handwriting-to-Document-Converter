import { useState } from "react";
import styles from "./LoginPage.module.css";

interface Props {
  onLogin: (email: string, password: string) => Promise<void>;
  onGoSignup: () => void;
  onGoForgotPassword: () => void;
}

export default function LoginPage({ onLogin, onGoSignup, onGoForgotPassword }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError("");
    if (!email.trim() || !password.trim()) {
      setError("이메일과 비밀번호를 입력해주세요.");
      return;
    }
    setLoading(true);
    try {
      await onLogin(email, password);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "로그인에 실패했습니다.";
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        setError("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSubmit();
  };

  return (
    <div className={styles.appContainer}>
      <div className={styles.header}>
        <div className={styles.appName}>필기 → 문서 변환기</div>
      </div>

      <div className={styles.formArea}>
        <h2 className={styles.title}>로그인</h2>

        <div className={styles.inputGroup}>
          <label className={styles.label}>이메일</label>
          <input
            type="email"
            className={styles.input}
            placeholder="이메일을 입력하세요"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        <div className={styles.inputGroup}>
          <label className={styles.label}>비밀번호</label>
          <input
            type="password"
            className={styles.input}
            placeholder="비밀번호를 입력하세요"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <button
          className={styles.loginButton}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "로그인 중..." : "로그인하기"}
        </button>
      </div>

      <div className={styles.bottomLinks}>
        <button className={styles.linkButton} onClick={onGoSignup}>
          회원가입
        </button>
        <span className={styles.divider}>|</span>
        <button className={styles.linkButton} onClick={onGoForgotPassword}>
          비밀번호 찾기
        </button>
      </div>

      <div className={styles.homeIndicator} />
    </div>
  );
}
