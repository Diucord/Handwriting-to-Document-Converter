import ScreenNav from './ScreenNav';
import styles from './ConversionPage.module.css';

interface Props {
  images: File[];
  progress: number;
  progressMessage: string;
  /** 파이프라인 현재 단계 (extract·classify·render·assemble) */
  stage?: string;
  /** 현재 단계의 세부 진행 (예: 3/8 페이지) */
  stageDetail?: { done: number; total: number } | null;
  /** 홈으로 나가기 (진행 중인 변환은 화면에서만 벗어납니다) */
  onHome?: () => void;
}

/**
 * 변환 화면.
 *
 * 이전에는 진행률 막대 하나만 보여줘서, 뒤에서 무슨 일이 일어나는지
 * 알 수 없었습니다. 실제로는 4단계 에이전트 파이프라인이 도는 구조이므로
 * 그 단계를 그대로 드러내 "지금 어디쯤인지"를 알 수 있게 했습니다.
 */

// 백엔드 STAGES 와 동일한 순서
const STAGES = [
  {
    key: 'extract',
    label: '텍스트 추출',
    desc: '페이지에서 글과 이미지 영역을 찾아냅니다',
  },
  {
    key: 'classify',
    label: '영역 분류',
    desc: '각 영역을 수식·다이어그램·차트·그림으로 판정합니다',
  },
  {
    key: 'render',
    label: '요소 재생성',
    desc: '판정 결과에 맞는 방식으로 다시 그립니다',
  },
  {
    key: 'assemble',
    label: '문서 조립',
    desc: '본문과 재생성된 요소를 합쳐 PDF 로 만듭니다',
  },
] as const;

export default function ConversionPage({
  images,
  progress,
  progressMessage,
  stage,
  stageDetail,
  onHome,
}: Props) {
  const currentIndex = STAGES.findIndex((s) => s.key === stage);

  return (
    <div className={styles['appContainer']}>
      <ScreenNav onHome={onHome} title="문서 변환" />
      <div className={styles['contentContainer']}>
        <header className={styles['header']}>
          <h2 className={styles['title']}>문서를 만들고 있습니다</h2>
          <p className={styles['subtitle']}>
            이미지 {images.length}장을 구조화된 문서로 변환합니다
          </p>
        </header>

        {/* 전체 진행률 */}
        <div className={styles['progressContainer']}>
          <div className={styles['progressBarBg']}>
            <div
              className={styles['progressBarFill']}
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className={styles['progressPercent']}>{progress}%</span>
        </div>

        {/* 4단계 파이프라인 */}
        <ol className={styles['stageList']}>
          {STAGES.map((s, i) => {
            const state =
              currentIndex < 0
                ? 'pending'
                : i < currentIndex
                ? 'done'
                : i === currentIndex
                ? 'active'
                : 'pending';

            return (
              <li key={s.key} className={`${styles['stage']} ${styles[state]}`}>
                <span className={styles['stageMark']} aria-hidden="true">
                  {state === 'done' ? '✓' : i + 1}
                </span>
                <span className={styles['stageBody']}>
                  <span className={styles['stageLabel']}>
                    {s.label}
                    {state === 'active' && stageDetail && (
                      <em className={styles['stageCount']}>
                        {stageDetail.done}/{stageDetail.total}
                      </em>
                    )}
                  </span>
                  <span className={styles['stageDesc']}>{s.desc}</span>
                </span>
              </li>
            );
          })}
        </ol>

        {progressMessage && (
          <p className={styles['progressMessage']}>{progressMessage}</p>
        )}
      </div>
    </div>
  );
}
