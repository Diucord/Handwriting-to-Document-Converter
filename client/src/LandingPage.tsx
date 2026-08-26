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
  X,
  Upload,
  Wand2,
  Download,
} from "lucide-react";
import Logo from "./Logo";
import Mockup from "./Mockup";
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

/* 기존 방식의 한계 → Notaformat 의 해결 (레퍼런스의 Before/After 대비 카드) */
const BEFORE = [
  "손글씨는 검색도 편집도 되지 않습니다",
  "그림과 수식은 사진으로 오려 붙입니다",
  "표와 차트는 처음부터 다시 그려야 합니다",
  "정리하는 데만 한 시간이 넘게 걸립니다",
];

const AFTER = [
  "글은 선택·검색 가능한 텍스트로 남습니다",
  "수식·다이어그램은 코드로 복원합니다",
  "차트는 축과 눈금까지 다시 그립니다",
  "사진을 올리면 나머지는 자동입니다",
];

/* 진한 파란 면에 놓이는 3단계 (레퍼런스의 화살표 연결 구조) */
const STEPS = [
  { icon: Upload, label: "사진 올리기", desc: "휴대폰으로 찍은 노트를 그대로 올립니다" },
  { icon: Wand2, label: "에이전트 처리", desc: "네 단계로 나눠 읽고 다시 그립니다" },
  { icon: Download, label: "문서 받기", desc: "완성된 PDF 를 내려받습니다" },
] as const;

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
            사진을 올리면 네 단계 에이전트가 글과 그림을 나눠 읽고,{" "}
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

          <Mockup />
        </div>
      </section>

      {/* ── Before / After 대비 ── */}
      <section className={styles["section"]}>
        <div className={styles["sectionInner"]}>
          <span className={styles["kicker"]}>왜 필요한가</span>
          <h2 className={styles["sectionTitle"]}>필기를 옮겨 적는 시간이 사라집니다</h2>

          <div className={styles["compare"]}>
            <div className={`${styles["compareCard"]} ${styles["compareBad"]}`}>
              <span className={styles["compareChip"]}>기존 방식</span>
              <h3 className={styles["compareTitle"]}>직접 옮겨 적기</h3>
              <ul className={styles["compareList"]}>
                {BEFORE.map((t) => (
                  <li key={t}>
                    <X size={15} strokeWidth={3} aria-hidden="true" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>

            <div className={`${styles["compareCard"]} ${styles["compareGood"]}`}>
              <span className={styles["compareChip"]}>Notaformat</span>
              <h3 className={styles["compareTitle"]}>사진 한 장이면 끝</h3>
              <ul className={styles["compareList"]}>
                {AFTER.map((t) => (
                  <li key={t}>
                    <Check size={15} strokeWidth={3} aria-hidden="true" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── 진한 파란 면 — 3단계.
           흰 면만 이어지면 스크롤이 단조로워 중간에 호흡을 끊습니다. ── */}
      <section className={styles["dark"]}>
        <div className={styles["sectionInner"]}>
          <span className={`${styles["kicker"]} ${styles["kickerOnDark"]}`}>
            시작하는 법
          </span>
          <h2 className={`${styles["sectionTitle"]} ${styles["onDark"]}`}>
            세 단계로 시작합니다
          </h2>
          <p className={`${styles["sectionSub"]} ${styles["onDarkSub"]}`}>
            설치할 것도, 배울 것도 없습니다. 사진만 준비하면 됩니다.
          </p>

          <ol className={styles["flow"]}>
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              return (
                <li key={s.label} className={styles["flowItem"]}>
                  <div className={styles["flowCard"]}>
                    <span className={styles["flowIcon"]} aria-hidden="true">
                      <Icon size={22} strokeWidth={2} />
                    </span>
                    <h3 className={styles["flowLabel"]}>{s.label}</h3>
                    <p className={styles["flowDesc"]}>{s.desc}</p>
                  </div>
                  {i < STEPS.length - 1 && (
                    <span className={styles["flowArrow"]} aria-hidden="true">
                      <ArrowRight size={20} strokeWidth={2.5} />
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
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

          {/* 좌우 교차 배치 — 카드 나열보다 읽는 순서가 분명합니다 */}
          <div className={styles["rows"]}>
            {PIPELINE.map((s, i) => {
              const Icon = s.icon;
              return (
                <div key={s.label} className={styles["row"]}>
                  <div className={styles["rowText"]}>
                    <span className={styles["rowNum"]}>STEP {i + 1}</span>
                    <h3 className={styles["rowTitle"]}>{s.label}</h3>
                    <p className={styles["rowDesc"]}>{s.desc}</p>
                  </div>
                  <div className={styles["rowVisual"]} aria-hidden="true">
                    <span className={styles["rowIcon"]}>
                      <Icon size={32} strokeWidth={1.7} />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 실제 화면 ── */}
      <section className={`${styles["section"]} ${styles["sectionAlt"]}`}>
        <div className={`${styles["sectionInner"]} ${styles["showcase"]}`}>
          <div className={styles["showcaseText"]}>
            <span className={styles["kicker"]}>실제 화면</span>
            <h2 className={styles["sectionTitle"]}>지금 어디까지 왔는지 보입니다</h2>
            <p className={styles["sectionSub"]}>
              막대 하나로 기다리게 두지 않습니다. 네 단계 중 어느 단계인지,
              그 안에서 몇 개를 처리했는지 그대로 드러냅니다.
            </p>

            <ul className={styles["showcaseList"]}>
              <li>
                <Check size={15} strokeWidth={3} aria-hidden="true" />
                단계별 진행 상태와 세부 카운트
              </li>
              <li>
                <Check size={15} strokeWidth={3} aria-hidden="true" />
                처리 중인 항목을 문장으로 안내
              </li>
              <li>
                <Check size={15} strokeWidth={3} aria-hidden="true" />
                완료된 단계는 초록 체크로 구분
              </li>
            </ul>
          </div>

          <div className={styles["showcaseShot"]}>
            <div className={styles["phone"]}>
              <img
                src="/app-conversion.png"
                alt="변환 진행 화면 — 네 단계 파이프라인과 진행률이 표시된 모습"
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── 재생성하는 요소 ── */}
      <section className={styles["section"]}>
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
