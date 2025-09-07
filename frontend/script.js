// Create animated background particles
      function createParticles() {
        const animation = document.querySelector('.bg-animation');
        for (let i = 0; i < 50; i++) {
          const particle = document.createElement('div');
          particle.className = 'particle';
          particle.style.left = Math.random() * 100 + '%';
          particle.style.top = Math.random() * 100 + '%';
          particle.style.animationDelay = Math.random() * 6 + 's';
          animation.appendChild(particle);
        }
      }
      
      createParticles();

      let audioContext;
      let processor;
      let input;
      let stream;
      let socket;
      let isAITalking = false;
      let audioBuffer = [];
      let silenceThreshold = 0.01;
      let silenceDuration = 1000;
      let silenceStartTime = null;
      let speaking = false;

      // UI helpers
      function updateStatus(text, type) {
        const status = document.getElementById("statusIndicator");
        const icon = type === 'listening' ? '🎙️' : type === 'speaking' ? '🔊' : '⏳';
        status.innerHTML = `<span class="mic-icon">${icon}</span> ${text}`;
        status.className = `status-indicator ${type}`;
      }

      function appendMessage(text, sender) {
        const chatBox = document.getElementById("chatBox");
        const div = document.createElement("div");
        div.className = `message ${sender}`;
        div.textContent = text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
      }

      function floatTo16BitPCM(input) {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
          output[i] = Math.max(-1, Math.min(1, input[i])) * 32767;
        }
        return output;
      }

      function encodeWAV(samples, sampleRate = 44100) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);

        const writeString = (offset, str) => {
          for (let i = 0; i < str.length; i++) {
            view.setUint8(offset + i, str.charCodeAt(i));
          }
        };

        writeString(0, "RIFF");
        view.setUint32(4, 36 + samples.length * 2, true);
        writeString(8, "WAVE");
        writeString(12, "fmt ");
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeString(36, "data");
        view.setUint32(40, samples.length * 2, true);

        const pcm = floatTo16BitPCM(samples);
        for (let i = 0; i < pcm.length; i++) {
          view.setInt16(44 + i * 2, pcm[i], true);
        }

        return new Blob([view], { type: "audio/wav" });
      }

      // Start Interview
      document.getElementById("startBtn").addEventListener("click", async () => {
        // Show chat interface
        document.getElementById("startSection").style.display = "none";
        document.getElementById("chatContainer").classList.add("active");
        document.getElementById("statusContainer").classList.add("active");

        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new AudioContext();
        input = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);

        socket = new WebSocket("ws://localhost:8000/ws/interview");
        socket.binaryType = "arraybuffer";

        let rawAudio = [];

        socket.onopen = () => {
          console.log("WebSocket connected");
          socket.send("__start__");
          updateStatus("Listening for your response", "listening");

          processor.onaudioprocess = (e) => {
            if (isAITalking) return;

            const inputData = e.inputBuffer.getChannelData(0);
            rawAudio.push(...inputData);

            const max = Math.max(...inputData.map((v) => Math.abs(v)));

            if (max > silenceThreshold) {
              silenceStartTime = null;
              speaking = true;
            } else if (speaking) {
              if (!silenceStartTime) silenceStartTime = Date.now();
              else if (Date.now() - silenceStartTime > silenceDuration) {
                speaking = false;
                silenceStartTime = null;

                processor.disconnect();
                input.disconnect();

                const wavBlob = encodeWAV(rawAudio);
                socket.send(wavBlob);
                socket.send("__end__");

                rawAudio = [];
                updateStatus("Processing your response<span class='loading-dots'></span>", "processing");
              }
            }
          };

          input.connect(processor);
          processor.connect(audioContext.destination);
        };

        socket.onmessage = async (event) => {
          if (typeof event.data === "string") {
            if (event.data.startsWith("TRANSCRIPT::")) {
              const userText = event.data.replace("TRANSCRIPT::", "").trim();
              appendMessage(userText, "user");
            } else if (event.data.startsWith("REPLY::")) {
              const replyText = event.data.replace("REPLY::", "").trim();
              appendMessage(replyText, "ai");
              isAITalking = true;
              updateStatus("AI is responding", "speaking");
            } else if (event.data === "__end__") {
              const blob = new Blob(audioBuffer, { type: "audio/mpeg" });
              const audioUrl = URL.createObjectURL(blob);
              const audio = new Audio(audioUrl);

              audio.onended = () => {
                isAITalking = false;
                audioBuffer = [];

                input.connect(processor);
                processor.connect(audioContext.destination);
                updateStatus("Listening for your response", "listening");
              };

              await audio.play();
            }
          } else {
            audioBuffer.push(event.data);
          }
        };

        socket.onerror = (err) => console.error("WebSocket error:", err);
        socket.onclose = () => console.log("WebSocket closed");
      });