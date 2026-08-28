import { useState, useRef } from "react";
import { SERVER_BASE_URL } from "./api";
import type { User } from "./useAuth";
import styles from "./ProfilePage.module.css";

interface Props {
  user: User;
  onBack: () => void;
  onLogout: () => void;
  onUpdateProfile: (data: { real_name?: string; nickname?: string }) => Promise<void>;
  onUploadProfileImage: (file: File) => Promise<void>;
}

export default function ProfilePage({
  user,
  onBack,
  onLogout,
  onUpdateProfile,
  onUploadProfileImage,
}: Props) {
  const [realName, setRealName] = useState(user.real_name);
  const [nickname, setNickname] = useState(user.nickname);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const profileSrc = user.profile_image_url
    ? `${SERVER_BASE_URL}${user.profile_image_url}`
    : "/profile.png";

  const handleSave = async () => {
    setError("");
    setSuccess("");

    if (!realName.trim()) { setError("실명을 입력해주세요."); return; }
    if (!nickname.trim()) { setError("닉네임을 입력해주세요."); return; }

    setSaving(true);
    try {
      await onUpdateProfile({ real_name: realName, nickname });
      setSuccess("저장되었습니다.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const handleImageClick = () => {
    fileInputRef.current?.click();
  };

  const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await onUploadProfileImage(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "이미지 업로드에 실패했습니다.");
    }
    e.target.value = "";
  };

  return (
    <div className={styles["appContainer"]}>
      <div className={styles["header"]}>
        <button className={styles["backButton"]} onClick={onBack}>
          ←
        </button>
        <div className={styles["appName"]}>내 정보</div>
      </div>

      <div className={styles["profileSection"]}>
        <div className={styles["avatarWrapper"]} onClick={handleImageClick}>
          <img src={profileSrc} alt="프로필" className={styles["avatar"]} />
          <div className={styles["cameraOverlay"]}>
            <span className={styles["cameraIcon"]}>📷</span>
          </div>
        </div>
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={handleImageChange}
        />
      </div>

      <div className={styles["formArea"]}>
        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>실명</label>
          <input
            type="text"
            className={styles["input"]}
            value={realName}
            onChange={(e) => setRealName(e.target.value)}
          />
        </div>

        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>닉네임</label>
          <input
            type="text"
            className={styles["input"]}
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
          />
        </div>

        <div className={styles["inputGroup"]}>
          <label className={styles["label"]}>이메일</label>
          <input
            type="email"
            className={styles["inputReadonly"]}
            value={user.email}
            readOnly
          />
        </div>

        {error && <div className={styles["error"]}>{error}</div>}
        {success && <div className={styles["success"]}>{success}</div>}

        <button
          className={styles["saveButton"]}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? "저장 중..." : "저장"}
        </button>

        <button className={styles["logoutButton"]} onClick={onLogout}>
          로그아웃
        </button>
      </div>

      <div className={styles["homeIndicator"]} />
    </div>
  );
}
