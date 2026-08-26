import styles from "./Mockup.module.css";

/**
 * 히어로의 변환 전후 목업.
 *
 * 이전에는 양쪽 다 회색 막대만 늘어놓아서, 무엇이 손글씨이고 무엇이
 * 정돈된 문서인지 구분되지 않았습니다. 여기서는 성격을 나눕니다.
 *
 *  왼쪽 — 실제 필기처럼 보이도록 SVG path 로 그린 획, 손으로 그린
 *         네모 그래프, 흘려 쓴 수식. 모눈종이 배경.
 *  오른쪽 — 제목/본문/조판된 수식/축이 있는 막대차트로 이루어진 문서.
 *
 * 둘 다 이미지가 아니라 코드라서 어느 해상도에서도 또렷합니다.
 */

/* 손으로 쓴 한 줄. seed 로 흔들림을 바꿔 같은 줄이 반복되지 않게 합니다. */
function InkLine({ width, seed = 0 }: { width: number; seed?: number }) {
  const w = 260 * (width / 100);
  const wob = (n: number) => Math.sin(seed * 2.3 + n) * 1.6;
  const d = `M2 ${9 + wob(0)}
     C ${w * 0.18} ${5 + wob(1)}, ${w * 0.3} ${12 + wob(2)}, ${w * 0.46} ${8.5 + wob(3)}
     S ${w * 0.72} ${5.5 + wob(4)}, ${w - 2} ${9 + wob(5)}`;
  return (
    <svg
      className={styles["inkLine"]}
      viewBox={`0 0 ${w} 18`}
      style={{ width: `${width}%` }}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path d={d} />
    </svg>
  );
}

export default function Mockup() {
  return (
    <div className={styles["mock"]}>
      {/* ── 손글씨 노트 ── */}
      <figure className={styles["col"]}>
        <figcaption className={styles["tag"]}>
          <span className={styles["dotAmber"]} aria-hidden="true" />
          손글씨 노트
        </figcaption>

        <div className={styles["paper"]}>
          {/* 제목처럼 크게 쓴 줄 */}
          <svg className={styles["inkTitle"]} viewBox="0 0 200 26" aria-hidden="true">
            <path d="M4 19 C 18 5, 26 22, 40 12 S 62 4, 74 17" />
            <path d="M88 18 C 98 6, 108 20, 120 11 S 140 6, 152 16" />
          </svg>

          <InkLine width={94} seed={1} />
          <InkLine width={78} seed={2} />

          {/* 손으로 그린 막대그래프 */}
          <svg className={styles["sketch"]} viewBox="0 0 240 96" aria-hidden="true">
            {/* 축 — 자로 대지 않은 듯 살짝 기울입니다 */}
            <path className={styles["axis"]} d="M22 8 L20 82 L226 79" />
            <path className={styles["bar"]} d="M44 80 L45 52 L70 51 L69 79 Z" />
            <path className={styles["bar"]} d="M88 79 L89 34 L114 33 L113 78 Z" />
            <path className={styles["bar"]} d="M132 78 L134 60 L158 59 L157 77 Z" />
            <path className={styles["bar"]} d="M176 77 L178 22 L202 21 L201 76 Z" />
          </svg>

          <InkLine width={88} seed={3} />

          {/* 흘려 쓴 수식 */}
          <svg className={styles["inkFormula"]} viewBox="0 0 190 30" aria-hidden="true">
            <path d="M8 24 C 4 14, 10 5, 16 6 C 22 7, 18 16, 12 20" />
            <path d="M26 8 L40 22 M40 8 L26 22" />
            <path d="M52 7 L52 23 M52 7 C 64 7, 66 14, 52 15 M52 15 C 66 15, 66 23, 52 23" />
            <path d="M78 15 L96 15" />
            <path d="M110 22 C 106 8, 118 6, 122 12 S 128 22, 134 16" />
            <path d="M146 8 L146 23 M146 8 L160 23 M160 8 L160 23" />
          </svg>

          <InkLine width={66} seed={4} />
        </div>
      </figure>

      {/* ── 화살표 ── */}
      <div className={styles["arrow"]} aria-hidden="true">
        <svg viewBox="0 0 24 24" width="20" height="20">
          <path
            d="M4 12h15M13 6l6 6-6 6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {/* ── 구조화된 문서 ── */}
      <figure className={styles["col"]}>
        <figcaption className={styles["tag"]}>
          <span className={styles["dotBlue"]} aria-hidden="true" />
          구조화된 PDF
        </figcaption>

        <div className={styles["doc"]}>
          <h4 className={styles["docTitle"]}>3. 실험 결과</h4>

          <p className={styles["docText"]}>
            분기별 처리량은 4분기에 가장 높게 나타났으며, 직전 분기 대비
            38% 증가했습니다.
          </p>

          {/* 축과 눈금이 있는 차트 */}
          <div className={styles["chart"]}>
            <div className={styles["chartGrid"]} aria-hidden="true">
              <span /> <span /> <span /> <span />
            </div>
            <div className={styles["bars"]}>
              {[38, 62, 47, 88].map((h, i) => (
                <div className={styles["barWrap"]} key={i}>
                  <div className={styles["barFill"]} style={{ height: `${h}%` }} />
                  <span className={styles["barLabel"]}>Q{i + 1}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 조판된 수식 */}
          <div className={styles["formula"]}>
            <span className={styles["fInt"]}>∫</span>
            <span>
              <em>f</em>(<em>x</em>)&thinsp;<em>dx</em> = <em>F</em>(<em>x</em>) +{" "}
              <em>C</em>
            </span>
          </div>

          <p className={styles["docText"]}>
            수식은 이미지가 아니라 텍스트로 남아 검색과 복사가 가능합니다.
          </p>
        </div>
      </figure>
    </div>
  );
}
