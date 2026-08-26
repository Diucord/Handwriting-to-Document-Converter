import {
  FileText,
  ScanLine,
  Sparkles,
  Layers,
  ShieldCheck,
  Gauge,
  Sigma,
  BarChart3,
  GitBranch,
  Image as ImageIcon,
  ArrowRight,
  Check,
} from "lucide-react";
import Logo from "./Logo";
import styles from "./LandingPage.module.css";

interface Props {
  /** 체험하기 — 로그인 없이 바로 변환 화면으로 */
  onStart: () => void;
  /** 로그인 화면으로 */
  onGoLogin: () => void;
  /** 로그인 상태면 상단 버튼 문구가 바뀝니다 */
  isLoggedIn: boolean;
}

/**
 * 랜딩 페이지.
 *
 * 기존 화면들은 전부 393px 모바일 고정이지만 이 페이지만 풀와이드입니다.
 * 처음 들어온 사람에게 무엇을 하는 서비스인지 먼저 설명하고
 * 체험하기로 앱에 진입시키는 역할이라, 앱 화면과 폭 규칙이 다릅니다.
 */

const PIPELINE = [
  {
    icon: ScanLine,
    label: "텍스트 추출",
    desc: "페이지에서 글과 이미지 영역을 찾아냅니다",
  },
  {
    icon: Layers,
    label: "영역 분류",
    desc: "수식·다이어그램·차트·그림 중 무엇인지 판정합니다",
  },
  {
    icon: Sparkles,
    label: "요소 재생성",
    desc: "판정 결과에 맞는 방식으로 다시 그립니다",
  },
  {
    icon: FileText,
    label: "문서 조립",
    desc: "본문과 재생성된 요소를 합쳐 PDF 로 만듭니다",
  },
] as const;

const ELEMENTS = [
  { icon: Sigma, title: "수식", desc: "LaTeX 로 다시 조판해 선명하게 넣습니다" },
  { icon: GitBranch, title: "다이어그램", desc: "Mermaid 코드로 복원해 선을 곧게 폅니다" },
  { icon: BarChart3, title: "차트", desc: "Chart.js 로 축과 눈금을 다시 그립니다" },
  { icon: ImageIcon, title: "그림", desc: "재생성이 어려우면 원본을 그대로 보존합니다" },
] as const;

const REASONS = [
  {
    icon: Gauge,
    title: "사진 한 장에서 바로",
    desc: "스캐너가 필요 없습니다. 휴대폰으로 찍은 노트를 그대로 올리면 됩니다.",
  },
  {
    icon: Sparkles,
    title: "그림까지 다시 그립니다",
    desc: "손으로 그린 도형과 수식을 이미지로 오려 붙이지 않고, 편집 가능한 형태로 되살립니다.",
  },
  {
    icon: ShieldCheck,
    title: "원본을 잃지 않습니다",
    desc: "재생성 신뢰도가 낮은 영역은 임의로 바꾸지 않고 원본을 유지합니다.",
  },
] as const;

export default function LandingPage({ onStart, onGoLogin, isLoggedIn }: Props) {
  return (
    <div className={styles["page"]}>
      {/* ── 상단 바 ── */}
      <header className={styles["topbar"]}>
        <div className={styles["topbarInner"]}>
          <Logo size={30} />
          <nav className={styles["topbarNav"]}>
            <button className={styles["ghostBtn"]} onClick={onGoLogin}>
              {isLoggedIn ? "내 문서함" : "로그인"}
            </button>
            <button className={styles["solidBtn"]} onClick={onStart}>
              체험하기
            </button>
          </nav>
        </div>
      </header>

      {/* ── 히어로 ── */}
      <section className={styles["hero"]}>
        <div className={styles["heroInner"]}>
          <span className={styles["badge"]}>
            <Sparkles size={13} strokeWidth={2.5} aria-hidden="true" />
            AI 에이전트 파이프라인
          </span>

          <h1 className={styles["heroTitle"]}>
            손으로 쓴 노트를,
            <br />
            <em className={styles["accent"]}>구조화된 문서로</em>
          </h1>

          <p className={styles["heroSub"]}>
            사진을 올리면 네 단계 에이전트가 글과 그림을 나눠 읽고,
            <br className={styles["brDesktop"]} />
            수식·다이어그램·차트를 다시 그려 PDF 로 만듭니다.
          </p>

          <div className={styles["heroActions"]}>
            <button className={styles["ctaPrimary"]} onClick={onStart}>
              무료로 체험하기
              <ArrowRight size={18} strokeWidth={2.5} aria-hidden="true" />
            </button>
            <button className={styles["ctaGhost"]} onClick={onGoLogin}>
              로그인
            </button>
          </div>

          <p className={styles["heroNote"]}>
            <Check size={14} strokeWidth={3} aria-hidden="true" />
            회원가입 없이 바로 변환해 볼 수 있습니다
          </p>

          {/* 목업 — 변환 전후 */}
          <div className={styles["mock"]}>
            <div className={styles["mockCol"]}>
              <span className={styles["mockTag"]}>손글씨 노트</span>
              <div className={`${styles["mockCard"]} ${styles["mockBefore"]}`}>
                <span className={styles["scribble"]} style={{ width: "82%" }} />
                <span className={styles["scribble"]} style={{ width: "94%" }} />
                <span className={styles["scribble"]} style={{ width: "70%" }} />
                <span className={styles["scribbleBox"]} />
                <span className={styles["scribble"]} style={{ width: "88%" }} />
                <span className={styles["scribble"]} style={{ width: "62%" }} />
              </div>
            </div>

            <div className={styles["mockArrow"]} aria-hidden="true">
              <ArrowRight size={22} strokeWidth={2.5} />
            </div>

            <div className={styles["mockCol"]}>
              <span className={styles["mockTag"]}>구조화된 PDF</span>
              <div className={`${styles["mockCard"]} ${styles["mockAfter"]}`}>
                <span className={styles["lineHead"]} />
                <span className={styles["line"]} style={{ width: "100%" }} />
                <span className={styles["line"]} style={{ width: "92%" }} />
                <span className={styles["formula"]}>∫ f(x) dx = F(x) + C</span>
                <span className={styles["line"]} style={{ width: "96%" }} />
                <span className={styles["line"]} style={{ width: "74%" }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 파이프라인 4단계 ── */}
      <section className={styles["section"]}>
        <div className={styles["sectionInner"]}>
          <span className={styles["kicker"]}>동작 방식</span>
          <h2 className={styles["sectionTitle"]}>네 단계로 문서가 됩니다</h2>
          <p className={styles["sectionSub"]}>
            한 번에 통째로 읽지 않고, 역할이 다른 에이전트가 순서대로 처리합니다.
          </p>

          <ol className={styles["steps"]}>
            {PIPELINE.map((s, i) => {
              const Icon = s.icon;
              return (
                <li key={s.label} className={styles["step"]}>
                  <span className={styles["stepNum"]}>{i + 1}</span>
                  <span className={styles["stepIcon"]} aria-hidden="true">
                    <Icon size={21} strokeWidth={2} />
                  </span>
                  <h3 className={styles["stepLabel"]}>{s.label}</h3>
                  <p className={styles["stepDesc"]}>{s.desc}</p>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      {/* ── 재생성하는 요소 ── */}
      <section className={`${styles["section"]} ${styles["sectionAlt"]}`}>
        <div className={styles["sectionInner"]}>
          <span className={styles["kicker"]}>재생성 대상</span>
          <h2 className={styles["sectionTitle"]}>그림을 사진으로 붙이지 않습니다</h2>
          <p className={styles["sectionSub"]}>
            영역마다 성격에 맞는 방식으로 다시 그리고, 어려우면 원본을 지킵니다.
          </p>

          <div className={styles["cards"]}>
            {ELEMENTS.map((e) => {
              const Icon = e.icon;
              return (
                <div key={e.title} className={styles["card"]}>
                  <span className={styles["cardIcon"]} aria-hidden="true">
                    <Icon size={20} strokeWidth={2} />
                  </span>
                  <h3 className={styles["cardTitle"]}>{e.title}</h3>
                  <p className={styles["cardDesc"]}>{e.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 선택 이유 ── */}
      <section className={styles["section"]}>
        <div className={styles["sectionInner"]}>
          <span className={styles["kicker"]}>특징</span>
          <h2 className={styles["sectionTitle"]}>Notaformat 을 쓰는 이유</h2>

          <div className={styles["reasons"]}>
            {REASONS.map((r) => {
              const Icon = r.icon;
              return (
                <div key={r.title} className={styles["reason"]}>
                  <span className={styles["reasonIcon"]} aria-hidden="true">
                    <Icon size={20} strokeWidth={2} />
                  </span>
                  <div className={styles["reasonBody"]}>
                    <h3 className={styles["reasonTitle"]}>{r.title}</h3>
                    <p className={styles["reasonDesc"]}>{r.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 마무리 CTA ── */}
      <section className={styles["cta"]}>
        <div className={styles["ctaInner"]}>
          <h2 className={styles["ctaTitle"]}>지금 노트 한 장으로 확인해보세요</h2>
          <p className={styles["ctaSub"]}>
            가입 절차 없이 사진을 올리면 바로 변환이 시작됩니다.
          </p>
          <button className={styles["ctaBig"]} onClick={onStart}>
            무료로 체험하기
            <ArrowRight size={19} strokeWidth={2.5} aria-hidden="true" />
          </button>
        </div>
      </section>

      <footer className={styles["footer"]}>
        <Logo size={26} />
        <p className={styles["footerNote"]}>손글씨를 구조화된 문서로</p>
      </footer>
    </div>
  );
}
