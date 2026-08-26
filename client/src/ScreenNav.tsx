import { ChevronLeft, Home } from "lucide-react";
import styles from "./ScreenNav.module.css";

interface Props {
  /** 뒤로가기 — 없으면 버튼을 숨깁니다 */
  onBack?: () => void;
  /** 홈(랜딩)으로 — 없으면 버튼을 숨깁니다 */
  onHome?: () => void;
  /** 가운데 표시할 화면 이름 */
  title?: string;
}

/**
 * 앱 화면 상단 내비게이션.
 *
 * 기존에는 변환·다운로드 화면에서 빠져나갈 방법이 다운로드 화면의
 * "홈으로 돌아가기" 하나뿐이었습니다. 화면마다 같은 자리에 뒤로가기와
 * 홈 버튼을 두어 어디서든 나갈 수 있게 합니다.
 */
export default function ScreenNav({ onBack, onHome, title }: Props) {
  return (
    <div className={styles["nav"]}>
      {onBack ? (
        <button className={styles["btn"]} onClick={onBack} aria-label="뒤로 가기">
          <ChevronLeft size={21} strokeWidth={2.2} />
        </button>
      ) : (
        <span className={styles["spacer"]} />
      )}

      {title && <span className={styles["title"]}>{title}</span>}

      {onHome ? (
        <button className={styles["btn"]} onClick={onHome} aria-label="홈으로">
          <Home size={18} strokeWidth={2.2} />
        </button>
      ) : (
        <span className={styles["spacer"]} />
      )}
    </div>
  );
}
