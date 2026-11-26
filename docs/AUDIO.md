# Audio: music and soundscape per area

All game audio added here is synthesized from code in `tools/audio/` (no recorded or third-party
samples), so it is ours to ship.

## Music

`Soundscape.music_for` (src/logic/soundscape.gd) picks the track per area, hour and weather; story
steps can override it. New themes from `tools/audio/make_music.py`:

| Track | Where |
|---|---|
| `harbor_day` | Dermaga, morning to afternoon (6/8 harbour waltz, musette reed + guitar) |
| `street_stroll` | Jalan Kota, morning to afternoon (swing stroll, electric piano) |
| `grandma_house` | Rumah Nenek Sari (3/4 music-box lullaby) |
| `gallery_light` | Galeri Komunitas (soft piano over a pad) |

## Soundscape (ambience)

`AreaSound` (src/area_sound.gd, a child of the `Audio` autoload) plays the area's profile from
`assets/audio/area_sound.json`:

- **layers**: 32 s seamless loops in `assets/audio/amb/` (wind, birds, crickets, cicadas, frogs,
  crowd, traffic, river, sea, rain on leaves/water/roof/street, cafe, kitchen, library, arcade,
  cave, clockwork, six dream pads...). Each has a `when` filter
  (`day, night, dawn, dusk, dry, rain, wind`) and fades in/out over ~3 s. A layer shared by two
  areas keeps playing through the door.
- **spots**: random one-shots in `assets/audio/spots/<id>_1..3.ogg` (gulls, creaking pier, buoy
  bell, ship horn, tokek, owl, woodpecker, dove, bike bell, train, crossing beeps, cup clinks,
  espresso, wall-clock chime, drips, crystal pings, thunder...). Random pitch, random side, and a
  reverb sized per place (`reverb`: room, hall, forest, cave, cathedral...).
- **positional loops**: fountains, waterfalls and campfires (by prop type, `emitters`), plus the
  area's `waterFlow` (river/sea, `flow`) and `water` ellipses (lake, `lake`). Volume and pan follow
  the player's distance.

Buses made at runtime: `Ambience`, `AmbVerb` (reverb) <- `AmbSpotL/C/R` (panners), `AmbEmit0..3`.

## Rebuilding

```
python3 tools/audio/make_soundscape.py          # loops + spots + area_sound.json (~1 min)
python3 tools/audio/make_soundscape.py json     # only the table after editing AREAS
python3 tools/audio/make_music.py [name]        # area themes
godot --headless --path . --import              # new .import files
GODOT=godot tools/audio/record_sample.sh out/   # short in-game tour video with sound
```

A new area needs an entry in `AREAS` (make_soundscape.py); the logic test checks every area has a
profile and every referenced file exists.
