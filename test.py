from faster_whisper import WhisperModel

model = WhisperModel(
    "large-v3-turbo",
    device= "cpu",
    compute_type="int8",
    cpu_threads=8,
    num_workers=1
)
audio = "test_audio/si519.wav"

if __name__ == '__main__':

    segments, info = model.transcribe(audio)
    # Detected language 'en' with probability 0.964498
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    # 生成器对象只能安全遍历一次，若需要多次遍历需要转为列表
    segments = list(segments)
    for segment in segments:
        # [0.00s -> 7.00s]  That added traffic means rising streams of dimes and quarters at tall games.
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

    print(len(list(segments)))