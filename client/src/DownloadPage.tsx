import { useEffect, useMemo } from "react";
import styles from './DownloadPage.module.css';

interface Props {
    images: File[];
    pdfUrl: string;
    wordUrl: string;
    exportFormat: "pdf" | "word";
    onFinish: () => void;
}

export default function DownloadPage({ images, pdfUrl, wordUrl, exportFormat, onFinish }: Props) {
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
            <div className={styles.contentWrapper}>

                <h2 className={styles.title}>문서 생성 완료!</h2>
                <p className={styles.message}>
                    {images.length}장의 이미지가 변환되었습니다
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
                            PDF 다운로드
                        </button>
                    )}
                    {exportFormat === "word" && wordUrl && (
                        <button
                            onClick={() => handleDownload(wordUrl, "converted_document.docx")}
                            className={styles.wordButton}
                        >
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
