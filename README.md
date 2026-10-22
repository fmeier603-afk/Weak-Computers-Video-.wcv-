# 🖥️ Weak Computers Video (.wcv)

**Weak Computers Video (.wcv)** is an experimental, high-performance, asymmetric video format designed specifically to bring smooth, high-resolution video playback to legacy and low-end hardware (such as vintage Core 2 Duo laptops) without requiring modern hardware acceleration or heavy codec decoding.

By shifting the computational burden entirely from the decoder to the encoder using **pixel-wise bitwise XOR operations**, `.wcv` achieves results that standard codecs on old hardware only dream of.

---

## 🚀 Performance Highlights

* **HD Resolution:** Smooth playback at `1280x720` resolution.
* **60 FPS Natively:** True 60 frames per second without stuttering or frame drops.
* **Extremely Low CPU Usage:** Runs at a mere **~9% CPU load** on legacy machines (e.g., Dell Latitude E5500).
* **No Hardware Acceleration Needed:** Bypasses missing HEVC/AVC decoders entirely through pure mathematical efficiency.
* **Zero Bloat:** Built with Python, NumPy (for C-speed vectorization), and FFmpeg.

---

## 💡 How It Works

Traditional video codecs require heavy, real-time decoding on the client side, which destroys the battery and CPU of older machines. `.wcv` flips the paradigm:

1. **The Reference Frame:** A static reference image (`referenz.png`) serves as the baseline.
2. **The XOR Transformation (Encoder):** During encoding, each raw video frame is bitwise XOR-ed against the reference frame (`frame XOR reference`).
3. **The Inverse XOR (Player):** On playback, the lightweight player reads the pre-computed stream chunk-by-chunk, applies a lightning-fast NumPy vectorized XOR operation, and pipes the uncompressed frames directly to `ffplay`.

Because bitwise XOR is its own inverse, decoding becomes nothing more than a trivial, ultra-fast binary mask application.

---

## 🛠️ Requirements

* Python 3.x
* NumPy
* FFmpeg / ffplay installed on your system

---

## 📁 Usage

### 1. Prepare your environment
Place your script, your target video, and a matching reference image (`referenz.png` in `1280x720`) in your working directory.

### 2. Encode a Video
Transform any standard video into the `.wcv` format:
```bash
python3 wcv_suite.py encode input_video.mp4
