interface Props {
  /** 심볼 한 변 크기(px) */
  size?: number;
  /** 이름을 함께 표시할지 */
  showName?: boolean;
  /** 글자색 (기본은 상속) */
  color?: string;
}

/**
 * Notaformat 로고.
 *
 * 손글씨 획(왼쪽 곡선)이 정돈된 문서 라인(오른쪽 직선)으로 바뀌는 형태로,
 * 서비스가 하는 일을 그대로 심볼에 담았습니다. png 대신 인라인 SVG 인 이유는
 * 크기·색을 쓰는 자리마다 다르게 줘야 하고, 배경이 밝은 곳과 어두운 곳
 * 양쪽에 올라가기 때문입니다.
 */
export default function Logo({ size = 28, showName = true, color }: Props) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: size * 0.32,
        color,
        lineHeight: 1,
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        role="img"
        aria-label="Notaformat"
      >
        <rect width="32" height="32" rx="9" fill="url(#nf-g)" />
        {/* 손글씨 획 */}
        <path
          d="M8.5 20.5c1.6-5.4 3.1-8.1 4.4-8.1 1.4 0 1.1 3.4-.6 6.6"
          stroke="#ffffff"
          strokeWidth="1.9"
          strokeLinecap="round"
          opacity="0.62"
        />
        {/* 정돈된 문서 라인 */}
        <rect x="16.4" y="11.2" width="8" height="1.9" rx="0.95" fill="#ffffff" />
        <rect x="16.4" y="15.05" width="8" height="1.9" rx="0.95" fill="#ffffff" />
        <rect x="16.4" y="18.9" width="5.2" height="1.9" rx="0.95" fill="#ffffff" />
        <defs>
          <linearGradient id="nf-g" x1="0" y1="0" x2="32" y2="32">
            <stop stopColor="#3b82f6" />
            <stop offset="1" stopColor="#4f46e5" />
          </linearGradient>
        </defs>
      </svg>

      {showName && (
        <span
          style={{
            fontSize: size * 0.58,
            fontWeight: 800,
            letterSpacing: "-0.02em",
            whiteSpace: "nowrap",
          }}
        >
          Notaformat
        </span>
      )}
    </span>
  );
}
