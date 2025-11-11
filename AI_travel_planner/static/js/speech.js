document.addEventListener('DOMContentLoaded', function() {
    // ... (existing code for form submission and modal)

    const micBtn = document.getElementById('mic-btn');
    const speechModal = document.getElementById('speech-modal');
    const speechText = document.getElementById('speech-text');
    const finishSpeechBtn = document.getElementById('finish-speech-btn');

    let mediaRecorder;
    let socket;
    let isRecording = false;
    let finalRecognizedText = "";

    micBtn.addEventListener('click', () => {
        speechModal.style.display = 'flex';
        startRecording();
    });

    finishSpeechBtn.addEventListener('click', () => {
        stopRecording();
        speechModal.style.display = 'none';
        if (finalRecognizedText) {
            extractInfoFromText(finalRecognizedText);
        }
    });

    function startRecording() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                isRecording = true;
                finalRecognizedText = "";
                speechText.textContent = '正在聆听...';
                micBtn.textContent = '🛑';

                mediaRecorder = new MediaRecorder(stream);
                const wsUrl = `ws://${window.location.host}/speech-to-text`;
                socket = new WebSocket(wsUrl);

                socket.onopen = () => {
                    console.log("WebSocket connection established.");
                    mediaRecorder.start(1280); // Send data every 1.28s
                };

                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                        socket.send(event.data);
                    }
                };

                socket.onmessage = event => {
                    const data = JSON.parse(event.data);
                    if (data.error) {
                        console.error("WebSocket Error:", data.error);
                        speechText.textContent = `错误: ${data.error}`;
                    } else if (data.intermediate_result) {
                        speechText.textContent = data.intermediate_result;
                    } else if (data.final_text) {
                        speechText.textContent = data.final_text;
                        finalRecognizedText = data.final_text;
                    }
                };

                socket.onerror = error => {
                    console.error("WebSocket Error:", error);
                    speechText.textContent = 'WebSocket 连接错误。';
                    isRecording = false;
                    micBtn.textContent = '语音输入';
                };

                socket.onclose = () => {
                    console.log("WebSocket connection closed.");
                    isRecording = false;
                    micBtn.textContent = '语音输入';
                };

            })
            .catch(err => {
                console.error("Error getting user media:", err);
                alert("无法获取麦克风权限，请检查设置。");
                speechModal.style.display = 'none';
            });
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
        isRecording = false;
        micBtn.textContent = '语音输入';
    }

    function extractInfoFromText(text) {
        document.getElementById('loader-modal').style.display = 'flex';
        fetch('/extract-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
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
        for (const key in info) {
            if (info[key] && document.getElementById(key)) {
                document.getElementById(key).value = info[key];
            }
        }
        alert("已根据您的语音输入自动填充表单！");
    }
});