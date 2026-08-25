import { useState } from "react";
import { apiPost } from "./api";
import styles from "./ForgotPasswordPage.module.css";

interface Props {
  onGoLogin: () => void;
}

export default function ForgotPasswordPage({ onGoLogin }: Props) {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError("");
    setMessage("");

    if (!email.trim()) {
      setError("이메일을 입력해주세요.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("올바른 이메일 형식이 아닙니다.");
      return;
    }

    setLoading(true);
    try {
      const res = await apiPost("/api/auth/forgot-password", { email });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "요청에 실패했습니다.");
      }
      setMessage("임시 비밀번호가 이메일로 전송되었습니다.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "요청에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.appContainer}>
      <div className={styles.header}>
        <button className={styles.backButton} onClick={onGoLogin}>
          ←
        </button>
        <div className={styles.appName}>비밀번호 찾기</div>
      </div>

      <div className={styles.formArea}>
        <p className={styles.description}>
          가입 시 사용한 이메일을 입력하시면
          <br />
          임시 비밀번호를 보내드립니다.
        </p>

        <div className={styles.inputGroup}>
          <label className={styles.label}>이메일</label>
          <input
            type="email"
            className={styles.input}
            placeholder="이메일을 입력하세요"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          />
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {message && <div className={styles.success}>{message}</div>}

        <button
          className={styles.submitButton}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "전송 중..." : "임시 비밀번호 받기"}
        </button>
      </div>

      <div className={styles.bottomLinks}>
        <button className={styles.linkButton} onClick={onGoLogin}>
          로그인으로 돌아가기
        </button>
      </div>

      <div className={styles.homeIndicator} />
    </div>
  );
}
