interface Props {
  /** 지름(px) */
  size?: number;
  /** 프로필 이미지 URL. 없으면 기본 아바타를 그립니다 */
  src?: string | null;
  /** 로그인한 사용자의 이름 — 있으면 첫 글자를 씁니다 */
  name?: string | null;
}

/**
 * 프로필 아바타.
 *
 * 비회원일 때 사진처럼 보이는 이미지가 들어가 있으면 "누군가로
 * 로그인된 상태"로 오해됩니다. 그래서 로그인하지 않았을 때는
 * 사람 실루엣을 그린 기본 아바타를 보여줍니다.
 *
 * 로그인했지만 사진을 올리지 않은 경우에는 이름 첫 글자를 씁니다.
 * 이름별로 배경색이 갈리므로 계정이 바뀐 것을 눈으로 알 수 있습니다.
 */

/* 이름에서 안정적으로 색을 뽑습니다 (같은 이름이면 항상 같은 색) */
const TONES = [
  { bg: "#e3f0ff", fg: "#1d6fd8" },
  { bg: "#e6f7ec", fg: "#1f8a4c" },
  { bg: "#fdecec", fg: "#c8393b" },
  { bg: "#f1ecfd", fg: "#6b46c1" },
  { bg: "#fff3e0", fg: "#b3651a" },
];

function toneFor(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return TONES[h % TONES.length]!;
}

export default function Avatar({ size = 30, src, name }: Props) {
  const base: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: "50%",
    flex: "none",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    boxSizing: "border-box",
  };

  /* 1) 올린 사진이 있으면 그대로 */
  if (src) {
    return (
      <span style={base}>
        <img
          src={src}
          alt=""
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </span>
    );
  }

  /* 2) 로그인했지만 사진이 없으면 이름 첫 글자 */
  const initial = name?.trim()?.[0];
  if (initial) {
    const tone = toneFor(name!.trim());
    return (
      <span
        style={{
          ...base,
          background: tone.bg,
          color: tone.fg,
          fontSize: size * 0.44,
          fontWeight: 700,
          letterSpacing: "-0.02em",
        }}
        aria-hidden="true"
      >
        {initial.toUpperCase()}
      </span>
    );
  }

  /* 3) 비회원 — 사람 실루엣 */
  return (
    <span
      style={{ ...base, background: "#e9ecf1", border: "1px solid #dfe3e9" }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 32 32" width={size} height={size}>
        <circle cx="16" cy="12.4" r="5.1" fill="#a8b0bd" />
        <path
          d="M5.6 29.4c0-5.9 4.7-9.6 10.4-9.6s10.4 3.7 10.4 9.6z"
          fill="#a8b0bd"
        />
      </svg>
    </span>
  );
}
