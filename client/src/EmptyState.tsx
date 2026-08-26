import styles from "./EmptyState.module.css";

interface Props {
  title: string;
  desc?: string;
  /** 비로그인 상태에서 보여줄 로그인 유도 버튼 */
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * 빈 상태 일러스트.
 *
 * 이전에는 "변환 기록이 없습니다" 라는 문장 하나뿐이라 화면이 비어
 * 보였습니다. 손글씨 노트가 문서로 바뀌는 장면을 작게 그려 넣어,
 * 기록이 없는 상태에서도 이 앱이 무엇을 하는지 읽히게 합니다.
 *
 * png 가 아니라 인라인 SVG 인 이유는 테마 색(--blue 등)을 그대로 쓰고
 * 어느 배율에서도 또렷해야 하기 때문입니다.
 */
export default function EmptyState({ title, desc, actionLabel, onAction }: Props) {
  return (
    <div className={styles["wrap"]}>
      <svg
        className={styles["art"]}
        viewBox="0 0 200 140"
        fill="none"
        role="img"
        aria-label="손글씨 노트가 문서로 바뀌는 그림"
      >
        {/* 뒤쪽 — 손글씨 노트 (기울여서 겹칩니다) */}
        <g transform="rotate(-8 66 74)">
          <rect
            x="30" y="30" width="72" height="88" rx="8"
            fill="#fdfbf6" stroke="#e6dfd0" strokeWidth="1.6"
          />
          {/* 펜 획 */}
          <g stroke="#a8a294" strokeWidth="2.2" strokeLinecap="round" fill="none">
            <path d="M42 48 C 50 44, 56 52, 64 47 S 78 43, 88 48" />
            <path d="M42 60 C 52 56, 58 64, 68 59 S 80 56, 90 60" />
            <path d="M42 96 C 50 92, 58 100, 68 95 S 80 92, 86 96" />
          </g>
          {/* 손으로 그린 작은 그래프 */}
          <g stroke="#a8a294" strokeWidth="1.8" strokeLinecap="round" fill="rgba(168,162,148,0.14)">
            <path d="M44 84 L43 72 L52 71 L53 83 Z" />
            <path d="M58 83 L57 66 L66 65 L67 82 Z" />
            <path d="M72 82 L71 76 L80 75 L81 81 Z" />
          </g>
        </g>

        {/* 앞쪽 — 구조화된 문서 */}
        <g>
          <rect
            x="98" y="24" width="74" height="92" rx="9"
            fill="#ffffff" stroke="#e2e5ea" strokeWidth="1.6"
          />
          {/* 제목 */}
          <rect x="110" y="38" width="32" height="6" rx="3" fill="#111827" />
          {/* 본문 */}
          <rect x="110" y="52" width="50" height="4" rx="2" fill="#e8eaed" />
          <rect x="110" y="61" width="44" height="4" rx="2" fill="#e8eaed" />
          {/* 조판된 차트 */}
          <g>
            <rect x="110" y="76" width="10" height="14" rx="2" fill="#9ecbff" />
            <rect x="124" y="70" width="10" height="20" rx="2" fill="#4da2ff" />
            <rect x="138" y="80" width="10" height="10" rx="2" fill="#9ecbff" />
            <rect x="152" y="66" width="10" height="24" rx="2" fill="#007aff" />
          </g>
          <rect x="110" y="100" width="46" height="4" rx="2" fill="#e8eaed" />
        </g>

        {/* 변환 화살표 */}
        <g transform="translate(86 66)">
          <circle r="13" fill="#ffffff" stroke="#e2e5ea" strokeWidth="1.4" />
          <path
            d="M-5 0 H5 M2 -3.5 L5.5 0 L2 3.5"
            stroke="#007aff" strokeWidth="2" strokeLinecap="round"
            strokeLinejoin="round" fill="none"
          />
        </g>
      </svg>

      <p className={styles["title"]}>{title}</p>
      {desc && <p className={styles["desc"]}>{desc}</p>}

      {actionLabel && onAction && (
        <button className={styles["action"]} onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
