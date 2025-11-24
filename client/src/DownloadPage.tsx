import { useState } from "react";
import styles from './DownloadPage.module.css'; // CSS Modules 임포트

interface Props {
    pdfUrl: string;
    onFinish: () => void;
}

export default function DownloadPage({ pdfUrl, onFinish }: Props) {
    const [isDownloaded, setIsDownloaded] = useState(false);

    const handleDownload = () => {
        const link = document.createElement("a");
        link.href = pdfUrl;
        link.download = "converted_document.pdf";
        link.click();

        setIsDownloaded(true);
    };

    return (
        // appContainer 스타일 적용 (모바일 뷰 중앙 정렬)
        <div className={styles.appContainer}>

            <div className={styles.contentWrapper}>
                
                {/* Download 아이콘 대신 /download.png 이미지 사용 */}
                <div className={styles.iconContainer}>
                    <img 
                        src="/download.png" 
                        alt="Download icon" 
                        className={styles.downloadIcon} 
                    />
                </div>

                <h2 className={styles.title}>
                    문서 생성 완료!
                </h2>
                <p className={styles.message}>
                    다운로드 버튼을 눌러 문서를 저장하세요.
                </p>

                <button
                    onClick={handleDownload}
                    className={styles.downloadButton}
                >
                    PDF 다운로드
                </button>

                {isDownloaded && (
                    <div className={styles.downloadCompleteText}>
                        다운로드가 완료되었습니다! ✔
                    </div>
                )}

                <button
                    onClick={onFinish}
                    className={styles.homeButton}
                >
                    홈으로 돌아가기
                </button>
            </div>
        </div>
    );
}