package org.womensafety.shield;

import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;

public class SirenPlayer {

    private AudioTrack audioTrack;
    private SoundThread soundThread;
    private volatile boolean isPlaying = false;
    private static final int SAMPLE_RATE = 44100;

    private static class SoundThread extends Thread {
        private final SirenPlayer player;

        public SoundThread(SirenPlayer player) {
            this.player = player;
        }

        @Override
        public void run() {
            int minBufferSize = AudioTrack.getMinBufferSize(
                    SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT
            );
            int bufferSize = Math.max(minBufferSize, SAMPLE_RATE / 2);

            AudioTrack track = new AudioTrack(
                    AudioManager.STREAM_ALARM,
                    SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    bufferSize,
                    AudioTrack.MODE_STREAM
            );

            try {
                track.play();
            } catch (Exception e) {
                player.isPlaying = false;
                return;
            }

            short[] buffer = new short[bufferSize];
            double phase = 0.0;
            long startTime = System.currentTimeMillis();

            while (player.isPlaying) {
                long elapsed = System.currentTimeMillis() - startTime;
                double cycle = (elapsed % 800) / 800.0;
                double freq = 650.0 + 400.0 * Math.sin(cycle * 2 * Math.PI);

                for (int i = 0; i < bufferSize; i++) {
                    buffer[i] = (short) (Math.sin(phase) * 32767);
                    phase += 2.0 * Math.PI * freq / SAMPLE_RATE;
                    if (phase > 2.0 * Math.PI) {
                        phase -= 2.0 * Math.PI;
                    }
                }
                track.write(buffer, 0, bufferSize);
            }

            try {
                track.stop();
                track.release();
            } catch (Exception ignored) {}
        }
    }

    public synchronized void play() {
        if (isPlaying) return;
        isPlaying = true;
        soundThread = new SoundThread(this);
        soundThread.start();
    }

    public synchronized void stop() {
        isPlaying = false;
        if (soundThread != null) {
            soundThread.interrupt();
            soundThread = null;
        }
    }

    public boolean isPlaying() {
        return isPlaying;
    }
}
