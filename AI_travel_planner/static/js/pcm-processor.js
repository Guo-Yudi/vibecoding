class PcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = [];
    // The iFlytek server expects 1280 bytes per 40ms frame.
    // At 16-bit (2 bytes) per sample, this is 640 samples.
    this.chunkSize = 640;
  }

  process(inputs, outputs, parameters) {
    // inputs[0][0] is a Float32Array of audio data.
    const channelData = inputs[0][0];

    if (channelData) {
      // Add new samples to our buffer
      this.buffer.push(...channelData);
    }

    // While we have enough samples for a full chunk, process and send it.
    while (this.buffer.length >= this.chunkSize) {
      const chunk = this.buffer.splice(0, this.chunkSize);
      const int16Chunk = new Int16Array(chunk.length);
      for (let i = 0; i < chunk.length; i++) {
        // Convert from Float32 [-1.0, 1.0] to Int16 [-32768, 32767]
        int16Chunk[i] = Math.max(-1, Math.min(1, chunk[i])) * 32767;
      }
      // Post the raw Int16Array buffer back to the main thread.
      // The second argument is a list of Transferable objects to move ownership, not copy.
      this.port.postMessage(int16Chunk.buffer, [int16Chunk.buffer]);
    }

    // Return true to let the browser know we want to keep processing.
    return true;
  }
}

registerProcessor('pcm-processor', PcmProcessor);