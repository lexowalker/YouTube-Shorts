# Pipeline

The scripts expect this working layout (the scratch folder used to build the Short):

```
src/source.mp4                 the long-form video (release asset `tao45`)
fonts/EBGaramond-500.ttf, -600.ttf   static instances of EB Garamond (OFL), from Google Fonts' variable font
img/raw/<accession>_full.jpg   CMA open-access masters (fetch with cma_get.py <dir> <accession> full)
work/                          intermediates
scripts/                       these files
```

Order:
1. `ffmpeg -i src/source.mp4 -ac 1 -ar 16000 work/audio16k.wav`
2. `transcribe.py` (full text) and `transcribe_ranges.py` (word timings for the chosen ranges; faster-whisper medium.en)
3. `build_edl.py`: segments, caption phrases with key words, and shot list. It asserts every caption word matches the spoken word
4. `crop_track.py work/edl.json src/source.mp4`: smoothed face-centred 9:16 crop path
5. `audio.py work/edl.json work/program_audio.wav`: joins, clean-up, −14 LUFS / −1.5 dBTP
6. `render.py work/edl.json work/video_master.mp4`: frames (head, stills, captions, title, end card)
7. Mux, 2-pass H.264 8 Mbps with AAC 256k (see DELIVERY.md)
