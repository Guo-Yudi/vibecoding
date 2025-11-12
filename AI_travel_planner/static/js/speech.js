document.addEventListener('DOMContentLoaded', function () {
    const micBtn = document.getElementById('mic-btn');
    const speechModal = document.getElementById('speech-modal');
    const closeBtn = document.getElementById('speech-close-btn');
    const speechText = document.getElementById('speech-text');
    const holdToTalkBtn = document.getElementById('hold-to-talk-btn');
    const confirmationButtons = document.getElementById('speech-confirmation-buttons');
    const confirmSpeechBtn = document.getElementById('confirm-speech-btn');
    const cancelSpeechBtn = document.getElementById('cancel-speech-btn');
    const finishSpeechBtn = document.getElementById('finish-speech-btn'); // This is now effectively replaced by the confirm/cancel buttons

    let socket;
    let audioContext;
    let microphone;
    let pcmProcessorNode;
    let isRecording = false;
    let finalRecognizedText = "";

    // Open the modal when the main mic button is clicked
    micBtn.addEventListener('click', () => {
        speechModal.style.display = 'flex';
        resetSpeechUI();
    });

    // Close the modal
    closeBtn.addEventListener('click', () => {
        stopRecording(); // Ensure recording stops
        speechModal.style.display = 'none';
    });

    // New confirmation logic
    function fillForm(info) {
        for (const key in info) {
            if (info[key] && document.getElementById(key)) {
                document.getElementById(key).value = info[key];
            }
        }
        alert("已根据您的语音输入自动填充表单！");
    }

    confirmSpeechBtn.addEventListener('click', () => {
        speechModal.style.display = 'none'; // Close speech modal immediately

        if (finalRecognizedText) {
            document.getElementById('loader-modal').style.display = 'flex';
            fetch('/process-speech-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: finalRecognizedText })
            })
            .then(response => response.json())
            .then(data => {
                if (data.extracted_info) {
                    fillForm(data.extracted_info);
                } else {
                    console.error('Failed to extract info from speech text:', data.error);
                    alert('未能从语音中提取有效信息，请手动填写。');
                }
            })
            .catch(error => {
                console.error('Error processing speech text:', error);
                alert('处理语音文本时出错，请手动填写。');
            })
            .finally(() => {
                document.getElementById('loader-modal').style.display = 'none';
            });
        }
    });

    cancelSpeechBtn.addEventListener('click', () => {
        speechModal.style.display = 'none';
    });

    // This button is hidden and its direct click logic is deprecated
    finishSpeechBtn.addEventListener('click', () => {
        // This is now a fallback, primarily triggered by the socket closing
        speechModal.style.display = 'none';
        if (finalRecognizedText) {
            extractInfoFromText(finalRecognizedText);
        }
    });

    // --- Hold-to-Talk Event Listeners ---
    holdToTalkBtn.addEventListener('mousedown', startRecording);
    holdToTalkBtn.addEventListener('mouseup', stopRecording);
    holdToTalkBtn.addEventListener('mouseleave', () => {
        if (isRecording) {
            stopRecording();
        }
    });
    holdToTalkBtn.addEventListener('touchstart', (e) => {
        e.preventDefault(); // Prevent firing mouse events
        startRecording();
    });
    holdToTalkBtn.addEventListener('touchend', stopRecording);


    async function startRecording() {
        if (isRecording) return;
        
        // Immediately update UI to show connection is in progress
        speechText.textContent = '正在连接，请稍候...';
        holdToTalkBtn.classList.add('recording'); // Use recording style for visual feedback

        try {
            // 1. Initialize WebSocket
            const wsUrl = `ws://${window.location.host}/ws/audio`;
            socket = new WebSocket(wsUrl);

            socket.onopen = async () => {
                console.log("WebSocket connection established.");
                // Now that connection is open, ask for mic and start listening
                speechText.textContent = '正在聆听...';
                isRecording = true;
                finalRecognizedText = "";

                try {
                    // 2. Initialize AudioContext and AudioWorklet
                    audioContext = new (window.AudioContext || window.webkitAudioContext)({
                        sampleRate: 16000
                    });

                    const stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000 } });
                    microphone = audioContext.createMediaStreamSource(stream);

                    await audioContext.audioWorklet.addModule('/static/js/pcm-processor.js');
                    pcmProcessorNode = new AudioWorkletNode(audioContext, 'pcm-processor');

                    // 3. Set up the processor to send data over WebSocket
                    pcmProcessorNode.port.onmessage = (event) => {
                        if (socket && socket.readyState === WebSocket.OPEN) {
                            socket.send(event.data);
                        }
                    };

                    // 4. Connect the audio graph
                    microphone.connect(pcmProcessorNode);

                } catch (err) {
                    console.error("Error during audio setup:", err);
                    alert("无法启动录音功能，请检查麦克风权限。\n" + err.message);
                    stopRecording(); // Clean up on error
                }
            };

            socket.onerror = error => {
                console.error("WebSocket Error:", error);
                speechText.textContent = '连接失败，请刷新重试。';
                holdToTalkBtn.classList.remove('recording');
            };

            socket.onclose = (event) => {
                console.log("WebSocket connection closed.", event.reason);
                if (isRecording) {
                    isRecording = false;
                    holdToTalkBtn.classList.remove('recording');
                }
                showConfirmationButtons();
            };

            socket.onmessage = event => {
                const data = JSON.parse(event.data);
                if (data.error) {
                    console.error("WebSocket Error from server:", data.error);
                    speechText.textContent = `错误: ${data.error}`;
                } else if (data.intermediate_result) {
                    speechText.textContent = data.intermediate_result;
                    finalRecognizedText = data.intermediate_result;
                } else if (data.final_text) {
                    speechText.textContent = data.final_text;
                    finalRecognizedText = data.final_text;
                }
            };

        } catch (err) {
            console.error("Error during WebSocket initialization:", err);
            speechText.textContent = '无法建立连接。';
            holdToTalkBtn.classList.remove('recording');
        }
    }

    async function stopRecording() {
        if (!isRecording) return;
        isRecording = false;
        speechText.textContent = '处理中...';
        holdToTalkBtn.classList.remove('recording');

        // Disconnect audio graph and stop tracks
        if (microphone) {
            microphone.mediaStream.getTracks().forEach(track => track.stop());
            microphone.disconnect();
            microphone = null;
        }
        if (pcmProcessorNode) {
            pcmProcessorNode.disconnect();
            pcmProcessorNode = null;
        }
        if (audioContext && audioContext.state !== 'closed') {
            await audioContext.close();
            console.log("AudioContext closed.");
            audioContext = null;
        }

        // Notify the server that the audio stream is ending
        if (socket && socket.readyState === WebSocket.OPEN) {
            // The server will send back the final text and then close the connection.
            // The client's `onclose` handler will then show the confirmation buttons.
            socket.send(JSON.stringify({ end_stream: true }));
            console.log("End of stream signal sent. Waiting for server to close connection.");
        } else {
             console.log("Socket not open or already closed. Showing confirmation buttons directly.");
             // If the socket is already closed, we can't send the end signal.
             showConfirmationButtons();
        }
    }

    function showConfirmationButtons() {
        holdToTalkBtn.style.display = 'none';
        confirmationButtons.style.display = 'flex';
        if (!finalRecognizedText) {
            speechText.textContent = "未能识别到语音，请重试。";
        }
    }

    function resetSpeechUI() {
        speechText.textContent = '按住按钮开始说话...';
        finalRecognizedText = "";
        holdToTalkBtn.style.display = 'flex';
        confirmationButtons.style.display = 'none';
        holdToTalkBtn.classList.remove('recording');
    }

    function extractInfoFromText(text) {
        // This function remains the same
        document.getElementById('loader-modal').style.display = 'flex';
        fetch('/extract-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text }),
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loader-modal').style.display = 'none';
            if (data.error) {
                alert(`信息提取失败: ${data.error}`);
            } else if (data.extracted_info) {
                fillForm(data.extracted_info);
            }
        })
        .catch(error => {
            document.getElementById('loader-modal').style.display = 'none';
            console.error('Error during extraction:', error);
            alert('提取信息时发生错误。');
        });
    }

    function fillForm(info) {
        // This function remains the same
        for (const key in info) {
            if (info[key] && document.getElementById(key)) {
                document.getElementById(key).value = info[key];
            }
        }
        alert("已根据您的语音输入自动填充表单！");
    }
});