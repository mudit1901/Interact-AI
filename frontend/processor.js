class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.silenceThreshold = 0.01;
    this.silenceFrames = 0;
    this.silenceFrameLimit = 15;
    this.recording = false;
  }

  process(inputs) {
    const input = inputs[0];
    if (input.length > 0) {
      const channel = input[0];
      const rms = Math.sqrt(
        channel.reduce((sum, sample) => sum + sample * sample, 0) /
          channel.length
      );

      if (rms > this.silenceThreshold) {
        this.silenceFrames = 0;
        this.recording = true;
        this.port.postMessage({
          event: "audio-chunk",
          buffer: new Float32Array(channel),
        });
      } else if (this.recording) {
        this.silenceFrames++;
        if (this.silenceFrames >= this.silenceFrameLimit) {
          this.recording = false;
          this.port.postMessage({ event: "audio-stop" });
        }
      }
    }
    return true;
  }
}

registerProcessor("audio-processor", AudioProcessor);
