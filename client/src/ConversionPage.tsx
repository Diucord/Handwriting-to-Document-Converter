import processingGif from "./assets/processing.gif";
import styles from './ConversionPage.module.css';

interface Props {
  images: File[];
  progress: number;
  progressMessage: string;
}

export default function ConversionPage({ images, progress, progressMessage }: Props) {
  return (
    <div className={styles['appContainer']}>
      <div className={styles['contentContainer']}>
        <img
          src={processingGif}
          className={styles['processingGif']}
          alt="processing"
        />
        <h2 className={styles['title']}>문서를 생성 중입니다…</h2>
        <p className={styles['message']}>{images.length}개의 이미지 변환중</p>

        <div className={styles['progressContainer']}>
          <div className={styles['progressBarBg']}>
            <div
              className={styles['progressBarFill']}
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className={styles['progressPercent']}>{progress}%</span>
        </div>

        {progressMessage && (
          <p className={styles['progressMessage']}>{progressMessage}</p>
        )}
      </div>
    </div>
  );
}
