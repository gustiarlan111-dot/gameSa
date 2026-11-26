#!/usr/bin/env bash
# Records a short in-game tour with sound (Godot Movie Maker) to hear the per-area soundscape.
#   GODOT=/path/to/godot tools/audio/record_sample.sh out_dir
# Each clip runs the real game in shot mode (walks between waypoints) for ~9 s at a fixed 30 fps,
# then all clips are joined into out_dir/contoh_suara_area.mp4 with a caption per area.
set -euo pipefail
GODOT=${GODOT:-godot}
OUT=${1:-build/sound_sample}
mkdir -p "$OUT"
FR=270
clip() {   # name caption minute day area x y waypoints
  local name=$1 cap=$2 minute=$3 day=$4 area=$5 x=$6 y=$7 wps=$8
  SHOT_MINUTE=$minute SHOT_DAY=$day timeout 600 xvfb-run -a -s "-screen 0 1280x720x24" "$GODOT" --path . --write-movie "$OUT/$name.avi" \
    --fixed-fps 30 --resolution 1280x720 -- --shot arland "$area" "$x" "$y" $FR "$OUT/$name.png" "$wps" > "$OUT/$name.log" 2>&1 || true
  ffmpeg -v error -y -i "$OUT/$name.avi" -vf "scale=960:540,drawtext=text='$cap':x=24:y=h-56:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10" \
    -c:v libx264 -crf 26 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 128k -ar 44100 "$OUT/$name.mp4"
  echo "file '$name.mp4'" >> "$OUT/list.txt"
}
rm -f "$OUT/list.txt"
clip 1_dermaga  "Dermaga siang - ombak, camar, kayu berderit" 600 1 dermaga 700 640 "1300:650"
clip 2_plaza    "Plaza - keramaian, burung, air mancur" 630 1 plaza 1200 700 "1200:880"
clip 3_jalan    "Jalan Kota siang - lalu lintas, lagu baru" 660 1 jalan_kota 604 559 "950:559"
clip 4_hutan    "Hutan Bisik malam - api unggun, jangkrik, burung hantu" 1290 1 hutan_bisik 1525 1640 "1525:1520"
clip 5_gua      "Gua Kristal - tetesan air bergema" 600 1 gua_kristal 640 880 "640:640"
clip 6_rumah    "Rumah Nenek Sari - jam dinding, lagu kotak musik" 600 1 rumah_sari 300 380 "300:260"
ffmpeg -v error -y -f concat -safe 0 -i "$OUT/list.txt" -c copy "$OUT/contoh_suara_area.mp4"
echo "$OUT/contoh_suara_area.mp4"
