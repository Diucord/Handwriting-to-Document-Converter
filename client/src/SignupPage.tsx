import { useState } from "react";
import { apiPost } from "./api";
import styles from "./SignupPage.module.css";

interface Props {
  onSignupComplete: () => void;
  onGoLogin: () => void;
}

export default function SignupPage({ onSignupComplete, onGoLogin }: Props) {
  const [realName, setRealName] = useState("");
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");

  // 핸드폰 인증 모달 상태
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verifyCode, setVerifyCode] = useState("");
  const [verifyPhone, setVerifyPhone] = useState("");
  const [verifyError, setVerifyError] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);

  const passwordMismatch = passwordConfirm.length > 0 && password !== passwordConfirm;

  const handleSendCode = async () => {
    setError("");

    if (!realName.trim()) { setError("실명을 입력해주세요."); return; }
    if (!nickname.trim()) { setError("닉네임을 입력해주세요."); return; }
    if (!email.trim()) { setError("이메일을 입력해주세요."); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError("올바른 이메일 형식이 아닙니다."); return; }
    if (!phoneNumber.trim()) { setError("핸드폰 번호를 입력해주세요."); return; }
    if (password.length < 8) { setError("비밀번호는 8자 이상이어야 합니다."); return; }
    if (password.length > 20) { setError("비밀번호는 20자 이하여야 합니다."); return; }
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)) { setError("비밀번호에 특수문자를 1개 이상 포함해주세요."); return; }
    if (password !== passwordConfirm) { setError("비밀번호가 일치하지 않습니다."); return; }

    setSendingCode(true);
    try {
      const res = await apiPost("/api/auth/signup", {
        real_name: realName,
        nickname,
        email,
        phone_number: phoneNumber,
        password,
        password_confirm: passwordConfirm,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "회원가입에 실패했습니다.");
      }
      setVerifyPhone(phoneNumber);
      setShowVerifyModal(true);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "회원가입에 실패했습니다.";
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        setError("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.");
      } else {
        setError(msg);
      }
    } finally {
      setSendingCode(false);
    }
  };

  const handleVerify = async () => {
    setVerifyError("");
    if (!verifyCode.trim()) { setVerifyError("인증 코드를 입력해주세요."); return; }

    setVerifying(true);
    try {
      const res = await apiPost("/api/auth/verify-phone", {
        phone_number: verifyPhone,
        code: verifyCode,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "인증에 실패했습니다.");
      }
      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      onSignupComplete();
    } catch (e) {
      setVerifyError(e instanceof Error ? e.message : "인증에 실패했습니다.");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className={styles["appContainer"]}>
      <div className={styles["header"]}>
        <button className={styles["backButton"]} onClick={onGoLogin}>
          ←
        </button>
        <div className={styles["appName"]}>회원가입</div>
      </div>

      <div className={styles["formArea"]}>
        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>실명 <span className={styles["required"]}>*</span></label>
          <input
            type="text"
            className={styles["input"]}
            placeholder="실명을 입력하세요"
            value={realName}
            onChange={(e) => setRealName(e.target.value)}
          />
        </div>

        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>닉네임 <span className={styles["required"]}>*</span></label>
          <input
            type="text"
            className={styles["input"]}
            placeholder="닉네임을 입력하세요"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
          />
        </div>

        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>이메일 <span className={styles["required"]}>*</span></label>
          <input
            type="email"
            className={styles["input"]}
            placeholder="이메일을 입력하세요"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>핸드폰 번호 <span className={styles["required"]}>*</span></label>
          <input
            type="tel"
            className={styles["input"]}
            placeholder="01012345678"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value.replace(/[^0-9]/g, ""))}
            maxLength={11}
          />
          <div className={styles["hint"]}>숫자만 입력 (예: 01012345678)</div>
        </div>

        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>비밀번호 <span className={styles["required"]}>*</span></label>
          <input
            type="password"
            className={styles["input"]}
            placeholder="비밀번호를 입력하세요"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            maxLength={20}
          />
          <div className={styles["hint"]}>8~20자, 특수문자 1개 이상 포함</div>
        </div>

        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>비밀번호 확인 <span className={styles["required"]}>*</span></label>
          <input
            type="password"
            className={`${styles["input"]} ${passwordMismatch ? styles["inputError"] : ""}`}
            placeholder="비밀번호를 다시 입력하세요"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            maxLength={20}
          />
          {passwordMismatch && (
            <div className={styles["fieldError"]}>비밀번호가 일치하지 않습니다.</div>
          )}
        </div>

        {error && <div className={styles["error"]}>{error}</div>}

        <button
          className={styles["verifyButton"]}
          onClick={handleSendCode}
          disabled={sendingCode || passwordMismatch}
        >
          {sendingCode ? "발송 중..." : "인증하기"}
        </button>
      </div>

      <div className={styles["bottomLinks"]}>
        <span className={styles["bottomText"]}>이미 계정이 있으신가요?</span>
        <button className={styles["linkButton"]} onClick={onGoLogin}>
          로그인
        </button>
      </div>

      {/* 핸드폰 인증 모달 */}
      {showVerifyModal && (
        <div className={styles["modalOverlay"]}>
          <div className={styles["modal"]}>
            <div className={styles["modalTitle"]}>핸드폰 인증</div>
            <p className={styles["modalDesc"]}>
              <strong>{verifyPhone}</strong> 으로<br />
              인증번호를 발송했습니다.<br />
              인증번호를 입력해주세요.
            </p>
            <input
              type="text"
              className={styles["modalInput"]}
              placeholder="인증 코드 6자리"
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              maxLength={6}
            />
            {verifyError && <div className={styles["fieldError"]}>{verifyError}</div>}
            <button
              className={styles["modalButton"]}
              onClick={handleVerify}
              disabled={verifying}
            >
              {verifying ? "확인 중..." : "인증 완료"}
            </button>
          </div>
        </div>
      )}

      <div className={styles["homeIndicator"]} />
    </div>
  );
}
