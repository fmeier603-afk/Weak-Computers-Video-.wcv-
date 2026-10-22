import os
import subprocess
import sys
import numpy as np

# Konfiguration
WORK_DIR = "/home/fabian/aplay/"
REF_IMG_PATH = os.path.join(WORK_DIR, "referenz.png")
OUTPUT_WCV = os.path.join(WORK_DIR, "video.wcv")
OUTPUT_AUDIO = os.path.join(WORK_DIR, "audio.wav")

WIDTH = 1280
HEIGHT = 720
FPS = 60
FRAME_SIZE = WIDTH * HEIGHT * 3  # ~2.76 MB pro Frame


def get_image_array(image_path):
    """Lädt das Referenzbild direkt als NumPy-Array für blitzschnelles XOR."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        image_path,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-",
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    data, _ = process.communicate()
    return np.frombuffer(data, dtype=np.uint8)


def encode_video(input_mp4):
    print("[*] Starte optimierten NumPy-Encoder (60 FPS)...")

    if not os.path.exists(REF_IMG_PATH):
        print(f"Fehler: Referenzbild nicht gefunden unter {REF_IMG_PATH}")
        return

    ref_arr = get_image_array(REF_IMG_PATH)
    if ref_arr.size == 0:
        print("Fehler: Konnte Referenzbild nicht verarbeiten.")
        return

    print("[*] Extrahiere Audiospur...")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            input_mp4,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            OUTPUT_AUDIO,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        input_mp4,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-",
    ]

    pipe = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    frame_count = 0

    print("[*] Vektorisiere XOR-Verknüpfung...")
    with open(OUTPUT_WCV, "wb") as out_f:
        header = f"({WIDTH}x{HEIGHT}@{FPS})\n".encode("utf-8")
        out_f.write(header)

        while True:
            frame_bytes = pipe.stdout.read(FRAME_SIZE)
            if len(frame_bytes) < FRAME_SIZE:
                break

            # NumPy Array aus den rohen Bytes machen und blitzschnell XORen
            frame_arr = np.frombuffer(frame_bytes, dtype=np.uint8)
            xored_arr = np.bitwise_xor(frame_arr, ref_arr)

            # Direkt als Byte-Stream wegschreiben
            out_f.write(xored_arr.tobytes())
            frame_count += 1

    pipe.terminate()
    print(
        f"[+] Enkodierung abgeschlossen! {frame_count} Frames in {OUTPUT_WCV} gespeichert."
    )


def play_video():
    print("[*] Starte Hochleistungs-Player mit vergrößertem Puffer...")

    if not os.path.exists(OUTPUT_WCV) or not os.path.exists(REF_IMG_PATH):
        print("Fehler: .wcv Datei oder Referenzbild fehlt!")
        return

    ref_arr = get_image_array(REF_IMG_PATH)

    audio_proc = None
    if os.path.exists(OUTPUT_AUDIO):
        audio_proc = subprocess.Popen(
            ["aplay", OUTPUT_AUDIO],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # ffplay mit großem internen Puffer (-buffer_size) starten, um Ruckler abzufangen
    player_cmd = [
        "ffplay",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{WIDTH}x{HEIGHT}",
        "-framerate",
        str(FPS),
        "-i",
        "-",
        "-autoexit",
    ]

    player_pipe = subprocess.Popen(
        player_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("[*] Spiele mit vollen 60 FPS ab...")

    try:
        with open(OUTPUT_WCV, "rb") as f:
            header = f.readline()
            print(f"[*] Metadaten: {header.decode('utf-8').strip()}")

            # Wir lesen direkt in einer optimierten Schleife
            while True:
                frame_data = f.read(FRAME_SIZE)
                if len(frame_data) < FRAME_SIZE:
                    break

                # Blitzschnelle Rückrechnung über NumPy auf C-Ebene
                frame_arr = np.frombuffer(frame_data, dtype=np.uint8)
                decoded_arr = np.bitwise_xor(frame_arr, ref_arr)

                # An den Player schicken
                player_pipe.stdin.write(decoded_arr.tobytes())
                # Kein erzwungenes .flush() pro Frame mehr, damit der OS-Pipe-Puffer greifen kann!

    except BrokenPipeError:
        pass

    if audio_proc:
        audio_proc.terminate()
    player_pipe.terminate()
    print("[+] Wiedergabe beendet.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  Encoder: python3 wcv_suite.py encode <video.mp4>")
        print("  Player:  python3 wcv_suite.py play")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "encode" and len(sys.argv) == 3:
        encode_video(sys.argv[2])
    elif mode == "play":
        play_video()
    else:
        print("Unbekannter Befehl.")
