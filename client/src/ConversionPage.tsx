import processingGif from "./assets/processing.gif";
import styles from './ConversionPage.module.css'; 

export default function ConversionPage({ images }: { images: File[] }) {
  return (
    // appContainer 스타일 적용 (모바일 뷰 중앙 정렬)
    <div className={styles.appContainer}> 
      <div className={styles.contentContainer}> 
        <img 
          src={processingGif} 
          className={styles.processingGif} 
          alt="processing"
        />
        <h2 className={styles.title}>문서를 생성 중입니다…</h2>
        <p className={styles.message}>{images.length}개의 이미지 변환중</p>
      </div>
    </div>
  );
}