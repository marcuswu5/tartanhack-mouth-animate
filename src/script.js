class MouthAnimator {
    constructor(mouthElement) {
        this.mouth = mouthElement;
        this.upperLip = mouthElement.querySelector('.upper-lip');
        this.lowerLip = mouthElement.querySelector('.lower-lip');
        this.innerMouth = mouthElement.querySelector('.inner-mouth');
        this.isAnimating = false;
    }

    startTalking() {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        this.mouth.classList.add('talking');
    }

    stopTalking() {
        this.isAnimating = false;
        this.mouth.classList.remove('talking');
        
        // Return to neutral state
        this.reset();
    }

    smile() {
        this.mouth.classList.remove('talking', 'open');
        this.mouth.classList.add('smiling');
    }

    open() {
        this.mouth.classList.remove('talking', 'smiling');
        this.mouth.classList.add('open');
    }

    reset() {
        this.stopTalking();
        this.mouth.classList.remove('smiling', 'open');
        // Reset to neutral closed mouth
        this.upperLip.setAttribute('d', 'M 20 35 Q 50 25 80 35');
        this.lowerLip.setAttribute('d', 'M 20 35 Q 50 45 80 35');
        this.innerMouth.setAttribute('d', 'M 20 35 Q 50 40 80 35');
        this.innerMouth.setAttribute('opacity', '0');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const mouthElement = document.querySelector('.mouth');
    const animator = new MouthAnimator(mouthElement);

    // Auto-start talking animation
    animator.startTalking();

    // Add click interaction
    mouthElement.addEventListener('click', () => {
        if (animator.isAnimating) {
            animator.stopTalking();
            setTimeout(() => animator.smile(), 200);
            setTimeout(() => animator.reset(), 2000);
        } else {
            animator.startTalking();
        }
    });

    // Keyboard controls
    document.addEventListener('keydown', (e) => {
        switch(e.key) {
            case ' ':
                e.preventDefault();
                if (animator.isAnimating) {
                    animator.stopTalking();
                } else {
                    animator.startTalking();
                }
                break;
            case 's':
                animator.smile();
                setTimeout(() => animator.reset(), 2000);
                break;
            case 'o':
                animator.open();
                setTimeout(() => animator.reset(), 1000);
                break;
        }
    });

    // Optional: Add hover effect
    mouthElement.addEventListener('mouseenter', () => {
        if (!animator.isAnimating) {
            animator.open();
        }
    });

    mouthElement.addEventListener('mouseleave', () => {
        if (!animator.isAnimating) {
            animator.reset();
        }
    });

    // Get all upload elements
    const videoUploadButton = document.getElementById('videoUploadButton');
    const videoUploadInput = document.getElementById('videoUpload');
    const audioUploadButton = document.getElementById('audioUploadButton');
    const audioUploadInput = document.getElementById('audioUpload');
    const framesUploadButton = document.getElementById('framesUploadButton');
    const framesUploadInput = document.getElementById('framesUpload');

    // Function to check if all files are uploaded and show/hide submit button
    function checkAllFilesUploaded() {
        const videoUploaded = videoUploadButton && videoUploadButton.classList.contains('uploaded');
        const audioUploaded = audioUploadButton && audioUploadButton.classList.contains('uploaded');
        const framesUploaded = framesUploadButton && framesUploadButton.classList.contains('uploaded');
        
        const submitSection = document.querySelector('.submit-section');
        if (submitSection) {
            if (videoUploaded && audioUploaded && framesUploaded) {
                submitSection.classList.add('visible');
            } else {
                submitSection.classList.remove('visible');
            }
        }
    }

    // Video upload functionality

    if (videoUploadButton && videoUploadInput) {
        videoUploadButton.addEventListener('click', (e) => {
            // Don't trigger if clicking the remove button
            if (e.target.closest('.remove-button')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('Video upload button clicked');
            videoUploadInput.click();
        });

        videoUploadInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                console.log('Video file selected:', file.name, file.type, file.size);
                videoUploadButton.classList.add('uploaded');
                checkAllFilesUploaded();
                // You can add file handling logic here
                // For example, preview, validation, or upload to server
            }
        });

        // Remove file functionality
        const videoRemoveButton = document.getElementById('videoRemoveButton');
        if (videoRemoveButton) {
            videoRemoveButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                videoUploadInput.value = '';
                videoUploadButton.classList.remove('uploaded');
                checkAllFilesUploaded();
                console.log('Video file removed');
            });
            // Allow Enter key to trigger remove
            videoRemoveButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    videoRemoveButton.click();
                }
            });
        }
    } else {
        console.error('Video upload elements not found:', { videoUploadButton, videoUploadInput });
    }

    // Audio upload functionality

    if (audioUploadButton && audioUploadInput) {
        audioUploadButton.addEventListener('click', (e) => {
            // Don't trigger if clicking the remove button
            if (e.target.closest('.remove-button')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('Audio upload button clicked');
            audioUploadInput.click();
        });

        audioUploadInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                console.log('Audio file selected:', file.name, file.type, file.size);
                audioUploadButton.classList.add('uploaded');
                checkAllFilesUploaded();
                // You can add file handling logic here
            }
        });

        // Remove file functionality
        const audioRemoveButton = document.getElementById('audioRemoveButton');
        if (audioRemoveButton) {
            audioRemoveButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                audioUploadInput.value = '';
                audioUploadButton.classList.remove('uploaded');
                checkAllFilesUploaded();
                console.log('Audio file removed');
            });
            // Allow Enter key to trigger remove
            audioRemoveButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    audioRemoveButton.click();
                }
            });
        }
    } else {
        console.error('Audio upload elements not found:', { audioUploadButton, audioUploadInput });
    }

    // Mouth frames upload functionality

    if (framesUploadButton && framesUploadInput) {
        framesUploadButton.addEventListener('click', (e) => {
            // Don't trigger if clicking the remove button
            if (e.target.closest('.remove-button')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('Frames upload button clicked');
            framesUploadInput.click();
        });

        framesUploadInput.addEventListener('change', (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
                console.log('Mouth frames selected:', files.length, 'file(s)');
                for (let i = 0; i < files.length; i++) {
                    console.log(`  - ${files[i].name} (${files[i].type}, ${files[i].size} bytes)`);
                }
                framesUploadButton.classList.add('uploaded');
                checkAllFilesUploaded();
                // You can add file handling logic here
            }
        });

        // Remove file functionality
        const framesRemoveButton = document.getElementById('framesRemoveButton');
        if (framesRemoveButton) {
            framesRemoveButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                framesUploadInput.value = '';
                framesUploadButton.classList.remove('uploaded');
                checkAllFilesUploaded();
                console.log('Mouth frames removed');
            });
            // Allow Enter key to trigger remove
            framesRemoveButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    framesRemoveButton.click();
                }
            });
        }
    } else {
        console.error('Frames upload elements not found:', { framesUploadButton, framesUploadInput });
    }

    // Submit button functionality
    const submitButton = document.getElementById('submitButton');
    const loadingPage = document.getElementById('loadingPage');
    const mainContainer = document.querySelector('.container');
    
    if (submitButton) {
        submitButton.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Submit button clicked');
            
            // Get all uploaded files
            const videoFile = videoUploadInput?.files[0];
            const audioFile = audioUploadInput?.files[0];
            const frameFiles = framesUploadInput?.files;
            
            if (videoFile && audioFile && frameFiles && frameFiles.length > 0) {
                console.log('All files ready for submission:');
                console.log('  Video:', videoFile.name);
                console.log('  Audio:', audioFile.name);
                console.log('  Frames:', frameFiles.length, 'file(s)');
                
                // Hide main container and show loading page
                if (mainContainer) {
                    mainContainer.style.display = 'none';
                }
                if (loadingPage) {
                    loadingPage.classList.add('visible');
                }
                
                // You can add submission logic here
                // For example, create FormData and send to server:
                // const formData = new FormData();
                // formData.append('video', videoFile);
                // formData.append('audio', audioFile);
                // for (let i = 0; i < frameFiles.length; i++) {
                //     formData.append('frames', frameFiles[i]);
                // }
                // fetch('/api/submit', { method: 'POST', body: formData })
                //     .then(response => response.json())
                //     .then(data => {
                //         // Handle success - maybe redirect or show result
                //     })
                //     .catch(error => {
                //         // Handle error - hide loading page and show error
                //         loadingPage.classList.remove('visible');
                //         mainContainer.style.display = 'block';
                //     });
            }
        });
    }
});
