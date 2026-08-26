import { useRef, useState, useEffect } from "react";
import { Home, Share2, Camera, FolderOpen, Images, ChevronRight } from "lucide-react";
import Logo from "./Logo";
import EmptyState from "./EmptyState";
import { apiGet, SERVER_BASE_URL } from "./api";
import type { User } from "./useAuth";
import styles from "./StartPage.module.css";

type ExportFormat = "pdf" | "word";

interface HistoryItem {
  id: number;
  title: string;
  file_type: string;
  file_url: string;
  created_at: string;
}

interface Props {
  user: User | null;
  sessionHistory: HistoryItem[];
  onImagesSelect: (files: File[], format: ExportFormat) => void;
  onGoLogin: () => void;
  onGoProfile: () => void;
  /** 랜딩(홈)으로 */
  onGoHome?: () => void;
}

export default function StartPage({ user, sessionHistory, onImagesSelect, onGoLogin, onGoProfile, onGoHome }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [showActionSheet, setShowActionSheet] = useState(false);
  const [showShareSheet, setShowShareSheet] = useState(false);
  const [copyToast, setCopyToast] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>("pdf");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filterMode, setFilterMode] = useState<"daily" | "monthly">("monthly");
  const [selectedDate, setSelectedDate] = useState(() => {
    const now = new Date();
    return now.toISOString().split("T")[0];
  });
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  const profileSrc = user?.profile_image_url
    ? `${SERVER_BASE_URL}${user.profile_image_url}`
    : "/profile.png";

  // 이력 불러오기
  useEffect(() => {
    if (!user) {
      setHistory([]);
      return;
    }

    const params =
      filterMode === "daily"
        ? `?date=${selectedDate}`
        : `?month=${selectedMonth}`;

    apiGet(`/api/history${params}`)
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("이력 조회 실패");
      })
      .then((data) => setHistory(data))
      .catch(() => setHistory([]));
  }, [user, filterMode, selectedDate, selectedMonth]);

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onImagesSelect(Array.from(e.target.files), exportFormat);
      setShowActionSheet(false);
      e.target.value = "";
    }
  };

  const handleCameraButtonClick = () => {
    cameraInputRef.current?.click();
  };

  const handleFileGalleryClick = () => {
    inputRef.current?.click();
  };

  const handleDocumentConvertClick = () => {
    setShowShareSheet(false);
    setShowActionSheet((prev) => !prev);
  };

  const handleShareClick = () => {
    setShowActionSheet(false);
    setShowShareSheet((prev) => !prev);
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.origin);
      setCopyToast(true);
      setTimeout(() => setCopyToast(false), 2000);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = window.location.origin;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopyToast(true);
      setTimeout(() => setCopyToast(false), 2000);
    }
  };

  const handleKakaoShare = () => {
    const url = encodeURIComponent(window.location.origin);
    const text = encodeURIComponent("필기 → 문서 변환 서비스를 확인해보세요!");
    window.open(
      `https://sharer.kakao.com/talk/friends/picker/shorturl?app_key=&url=${url}&text=${text}`,
      "_blank",
      "width=500,height=600"
    );
  };

  const handleEmailShare = () => {
    const subject = encodeURIComponent("필기 → 문서 변환 서비스");
    const body = encodeURIComponent(
      `필기 → 문서 변환 서비스를 확인해보세요!\n\n${window.location.origin}`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  const handleHistoryClick = (item: HistoryItem) => {
    // 세션 기록은 이미 full URL, DB 기록은 상대 경로
    const url = item.file_url.startsWith("http")
      ? item.file_url
      : `${SERVER_BASE_URL}${item.file_url}`;
    window.open(url, "_blank");
  };

  const formatDateTime = (isoString: string) => {
    const d = new Date(isoString);
    const date = `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
    const time = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    return { date, time };
  };

  return (
    <div className={styles.appContainer}>
      <div className={styles.header}>
        <button
          className={styles.appName}
          onClick={onGoHome}
          aria-label="홈으로"
        >
          <Logo size={26} />
        </button>
        <div className={styles.headerRight}>
          <span
            className={styles.loginText}
            onClick={user ? undefined : onGoLogin}
          >
            {user ? user.nickname : "로그인하기"}
          </span>
          <div
            className={styles.profileImage}
            onClick={user ? onGoProfile : onGoLogin}
          >
            <img
              src={profileSrc}
              alt="profile"
              className={styles.profileImg}
            />
          </div>
        </div>
      </div>

      <div className={styles.tabs}>
        <div className={styles.tabActive}>내 문서</div>
        <button className={styles.tabInactive}>공유 문서</button>
      </div>

      {user ? (
        <>
          {/* 날짜 필터 */}
          <div className={styles.filterBar}>
            <div className={styles.filterToggle}>
              <button
                className={`${styles.filterButton} ${filterMode === "daily" ? styles.filterButtonActive : ""}`}
                onClick={() => setFilterMode("daily")}
              >
                일별
              </button>
              <button
                className={`${styles.filterButton} ${filterMode === "monthly" ? styles.filterButtonActive : ""}`}
                onClick={() => setFilterMode("monthly")}
              >
                월별
              </button>
            </div>
            <div className={styles.dateSelector}>
              {filterMode === "daily" ? (
                <input
                  type="date"
                  className={styles.dateInput}
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                />
              ) : (
                <input
                  type="month"
                  className={styles.dateInput}
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(e.target.value)}
                />
              )}
            </div>
          </div>

          {/* 이력 목록 (DB + 세션 기록 합산) */}
          {(history.length > 0 || sessionHistory.length > 0) ? (
            <div className={styles.historyContent}>
              <div className={styles.historyList}>
                {[...sessionHistory, ...history]
                  .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                  .map((item) => {
                  const { date, time } = formatDateTime(item.created_at);
                  return (
                    <div
                      key={`${item.id}-${item.file_type}`}
                      className={styles.historyItem}
                      onClick={() => handleHistoryClick(item)}
                    >
                      <div className={styles.historyLeft}>
                        <div className={styles.historyTitle}>{item.title}</div>
                        <div className={styles.historyFileType}>
                          {item.file_type.toUpperCase()}
                        </div>
                      </div>
                      <div className={styles.historyRight}>
                        <div className={styles.historyDate}>{date}</div>
                        <div className={styles.historyTime}>{time}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className={styles.message}>
              <EmptyState
                title="해당 기간의 변환 기록이 없습니다"
                desc="날짜를 바꾸거나 새 문서를 변환해 보세요."
              />
            </div>
          )}
        </>
      ) : (
        <>
          {sessionHistory.length > 0 ? (
            <div className={styles.historyContent}>
              <div className={styles.historyList}>
                {sessionHistory.map((item) => {
                  const { date, time } = formatDateTime(item.created_at);
                  return (
                    <div
                      key={item.id}
                      className={styles.historyItem}
                      onClick={() => handleHistoryClick(item)}
                    >
                      <div className={styles.historyLeft}>
                        <div className={styles.historyTitle}>{item.title}</div>
                        <div className={styles.historyFileType}>
                          {item.file_type.toUpperCase()}
                        </div>
                      </div>
                      <div className={styles.historyRight}>
                        <div className={styles.historyDate}>{date}</div>
                        <div className={styles.historyTime}>{time}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className={styles.message}>
              <EmptyState
                title="아직 변환한 문서가 없습니다"
                desc={"손글씨 노트를 올리면 구조화된 문서로 만들어 드립니다.\n로그인하면 기록이 영구 보관됩니다."}
                actionLabel="로그인하기"
                onAction={onGoLogin}
              />
            </div>
          )}
        </>
      )}

      <div
        className={`${styles.actionSheet} ${showActionSheet ? styles.actionSheetVisible : styles.actionSheetHidden}`}
      >
        <div className={styles.actionButtons}>
          <div className={styles.actionSheetTitle}>
            변환할 형식을 선택하세요
          </div>

          <div className={styles.formatToggle}>
            <button
              className={`${styles.formatButton} ${exportFormat === "pdf" ? styles.formatButtonActive : ""}`}
              onClick={() => setExportFormat("pdf")}
            >
              PDF
            </button>
            <button
              className={`${styles.formatButton} ${exportFormat === "word" ? styles.formatButtonActive : ""}`}
              onClick={() => setExportFormat("word")}
            >
              Word
            </button>
          </div>

          <div className={styles.actionSheetSubtitle}>
            문서를 가져올 경로를 선택하세요
          </div>

          <button
            onClick={handleCameraButtonClick}
            className={`${styles.actionButton} ${styles.cameraButton}`}
          >
            <span className={styles["actionIcon"]} aria-hidden="true">
              <Camera size={19} strokeWidth={2} />
            </span>
            <span className={styles["actionLabel"]}>카메라</span>
            <ChevronRight size={17} strokeWidth={2.2} className={styles["actionChev"]} aria-hidden="true" />
          </button>

          <button
            onClick={handleFileGalleryClick}
            className={`${styles.actionButton} ${styles.fileButton}`}
          >
            <span className={styles["actionIcon"]} aria-hidden="true">
              <FolderOpen size={19} strokeWidth={2} />
            </span>
            <span className={styles["actionLabel"]}>파일</span>
            <ChevronRight size={17} strokeWidth={2.2} className={styles["actionChev"]} aria-hidden="true" />
          </button>

          <button
            onClick={handleFileGalleryClick}
            className={`${styles.actionButton} ${styles.galleryButton}`}
          >
            <span className={styles["actionIcon"]} aria-hidden="true">
              <Images size={19} strokeWidth={2} />
            </span>
            <span className={styles["actionLabel"]}>갤러리</span>
            <ChevronRight size={17} strokeWidth={2.2} className={styles["actionChev"]} aria-hidden="true" />
          </button>
        </div>
      </div>

      <input
        type="file"
        accept="image/*"
        ref={inputRef}
        className={styles.inputHidden}
        multiple
        onChange={handleSelect}
      />

      <input
        type="file"
        accept="image/*"
        capture="environment"
        ref={cameraInputRef}
        className={styles.inputHidden}
        multiple
        onChange={handleSelect}
      />

      {showShareSheet && (
        <div className={styles["shareOverlay"]} onClick={() => setShowShareSheet(false)} />
      )}

      <div
        className={`${styles["shareSheet"]} ${showShareSheet ? styles["shareSheetVisible"] : styles["shareSheetHidden"]}`}
      >
        <div className={styles["shareSheetTitle"]}>공유하기</div>
        <div className={styles["shareOptions"]}>
          <button className={styles["shareOption"]} onClick={handleCopyLink}>
            <div className={styles["shareIconCircle"]} style={{ backgroundColor: "#f3f4f6" }}>
              <span className={styles["shareEmoji"]}>🔗</span>
            </div>
            <span className={styles["shareLabel"]}>링크 복사</span>
          </button>
          <button className={styles["shareOption"]} onClick={handleKakaoShare}>
            <div className={styles["shareIconCircle"]} style={{ backgroundColor: "#FEE500" }}>
              <span className={styles["shareEmoji"]}>💬</span>
            </div>
            <span className={styles["shareLabel"]}>카카오톡</span>
          </button>
          <button className={styles["shareOption"]} onClick={handleEmailShare}>
            <div className={styles["shareIconCircle"]} style={{ backgroundColor: "#e0f2fe" }}>
              <span className={styles["shareEmoji"]}>✉️</span>
            </div>
            <span className={styles["shareLabel"]}>메일</span>
          </button>
        </div>
      </div>

      {copyToast && (
        <div className={styles["toast"]}>링크가 복사되었습니다</div>
      )}

      <div className={styles.navBar}>
        <button className={styles.navButton} onClick={onGoHome} aria-label="홈">
          <Home size={21} strokeWidth={2} className={styles.navIcon} />
        </button>

        <button
          onClick={handleDocumentConvertClick}
          className={styles.convertButton}
        >
          문서 변환
        </button>

        <button className={styles.navButton} onClick={handleShareClick} aria-label="공유">
          <Share2 size={20} strokeWidth={2} className={styles.navIcon} />
        </button>
      </div>

      <div className={styles.homeIndicator} />
    </div>
  );
}
