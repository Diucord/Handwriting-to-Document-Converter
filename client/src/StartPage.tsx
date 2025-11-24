import { useRef, useState } from "react";
import styles from './StartPage.module.css';

interface Props {
    onImagesSelect: (files: File[]) => void;
}

interface DocumentItem {
    id: number;
    title: string;
    date: string; 
}

export default function StartPage({ onImagesSelect }: Props) {
    const inputRef = useRef<HTMLInputElement>(null);
    const cameraInputRef = useRef<HTMLInputElement>(null);
    const [showActionSheet, setShowActionSheet] = useState(false); 
    const [documentHistory, setDocumentHistory] = useState<DocumentItem[]>([]); 

    const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            onImagesSelect(Array.from(e.target.files));
            setShowActionSheet(false);
            
            const now = new Date();
            const formattedDate = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')}`;
            
            const selectedFileName = e.target.files[0].name || "선택 파일";
            const simulatedKeywords = "새 필기문서"; 
            const newTitle = `${simulatedKeywords} (${selectedFileName.substring(0, selectedFileName.length > 15 ? 15 : selectedFileName.length)})`;

            const newDocument: DocumentItem = {
                id: Date.now(),
                title: newTitle,
                date: formattedDate,
            };

            setDocumentHistory(prev => [newDocument, ...prev]);
            
            e.target.value = '';
        }
    };
    
    const handleCameraButtonClick = () => {
        cameraInputRef.current?.click();
    }

    const handleFileGalleryClick = () => {
        inputRef.current?.click();
    }

    const handleDocumentConvertClick = () => {
        setShowActionSheet(prev => !prev);
    }

    return (
        <div className={styles.appContainer}>
        
        <div className={styles.header}>
            <div className={styles.appName}>필기 → 문서 변환기</div>
            <div className={styles.profileImage}>
                <img
                    src="/profile.png" 
                    alt="profile"
                    className="w-full h-full object-cover"
                />
            </div>
        </div>

        <div className={styles.tabs}>
            <div className={styles.tabActive}>내 문서</div>
            <button className={styles.tabInactive}>공유 문서</button>
        </div>

        {documentHistory.length > 0 ? (
            <div className={styles.historyContent}>
                <div className={styles.historyList}>
                    {documentHistory.map(doc => (
                        <div key={doc.id} className={styles.historyItem}>
                            <div>{doc.title}</div>
                            <div className={styles.historyDate}>{doc.date}</div>
                        </div>
                    ))}
                </div>
            </div>
        ) : (
            <div className={styles.message}>
                문서 변환을 <br /> 시작해보세요
            </div>
        )}

        <div 
            className={`${styles.actionSheet} ${showActionSheet ? styles.actionSheetVisible : styles.actionSheetHidden}`}
        >
            <div className={styles.actionButtons}>
                <div className={styles.actionSheetTitle}>
                    문서를 가져올 경로를 선택하세요
                </div>

                <button 
                    onClick={handleCameraButtonClick}
                    className={`${styles.actionButton} ${styles.cameraButton}`}
                >
                    카메라
                </button>

                <button
                    onClick={handleFileGalleryClick}
                    className={`${styles.actionButton} ${styles.fileButton}`}
                >
                    파일
                </button>

                <button 
                    onClick={handleFileGalleryClick}
                    className={`${styles.actionButton} ${styles.galleryButton}`}
                >
                    갤러리
                </button>
            </div>
        </div>
        
        <input
            type="file"
            accept="image/*" 
            ref={inputRef}
            className={styles.inputHidden}
            multiple
            onChange={handleSelect}
        />
        
        <input
            type="file"
            accept="image/*"
            capture="environment" 
            ref={cameraInputRef}
            className={styles.inputHidden}
            multiple
            onChange={handleSelect}
        />
        
        <div className={styles.navBar}>
            <button className={styles.navButton}>
                <img src="/home.png" alt="홈" className={styles.navIcon} />
            </button>

            <button 
                onClick={handleDocumentConvertClick}
                className={styles.convertButton}
            >
                문서 변환
            </button>

            <button className={styles.navButton}>
                <img src="/share.png" alt="공유" className={styles.navIcon} />
            </button>
        </div>
        
        <div className={styles.homeIndicator} />
        </div>
    );
}