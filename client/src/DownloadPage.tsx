import { useEffect, useMemo } from "react";
import { CircleCheck, Download } from "lucide-react";
import ScreenNav from './ScreenNav';
import styles from './DownloadPage.module.css';

interface Props {
    images: File[];
    pdfUrl: string;
    wordUrl: string;
    exportFormat: "pdf" | "word";
    onFinish: () => void;
    /** 업로드 화면으로 되돌아가기 */
    onBack?: () => void;
}

export default function DownloadPage({ images, pdfUrl, wordUrl, exportFormat, onFinish, onBack }: Props) {
    // 썸네일 ObjectURL 생성 및 컴포넌트 언마운트 시 해제
    const thumbnailUrls = useMemo(
        () => images.map((f) => URL.createObjectURL(f)),
        [images]
    );
    useEffect(() => {
        return () => thumbnailUrls.forEach((url) => URL.revokeObjectURL(url));
    }, [thumbnailUrls]);

    const handleDownload = (url: string, filename: string) => {
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        link.click();
    };

    return (
        <div className={styles.appContainer}>
            <ScreenNav onBack={onBack} onHome={onFinish} title="변환 완료" />
            <div className={styles.contentWrapper}>

                <span className={styles["badge"]} aria-hidden="true">
                    <CircleCheck size={38} strokeWidth={2} />
                </span>

                <h2 className={styles.title}>문서가 완성되었습니다</h2>
                <p className={styles.message}>
                    이미지 {images.length}장을 구조화된 문서로 변환했습니다.
                </p>

                {/* 원본 이미지 썸네일 그리드 */}
                <div className={styles.thumbnailGrid}>
                    {thumbnailUrls.map((url, i) => (
                        <img
                            key={i}
                            src={url}
                            alt={`이미지 ${i + 1}`}
                            className={styles.thumbnail}
                        />
                    ))}
                </div>

                {/* 선택한 포맷에 따라 다운로드 버튼 표시 */}
                <div className={styles.buttonRow}>
                    {exportFormat === "pdf" && pdfUrl && (
                        <button
                            onClick={() => handleDownload(pdfUrl, "converted_document.pdf")}
                            className={styles.pdfButton}
                        >
                            <Download size={18} strokeWidth={2.3} aria-hidden="true" />
                            PDF 다운로드
                        </button>
                    )}
                    {exportFormat === "word" && wordUrl && (
                        <button
                            onClick={() => handleDownload(wordUrl, "converted_document.docx")}
                            className={styles.wordButton}
                        >
                            <Download size={18} strokeWidth={2.3} aria-hidden="true" />
                            Word 다운로드
                        </button>
                    )}
                </div>

                <button onClick={onFinish} className={styles.homeButton}>
                    홈으로 돌아가기
                </button>
            </div>
        </div>
    );
}
