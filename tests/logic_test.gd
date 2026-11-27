extends Node
## Headless logic checks for the Godot port:  godot --headless --path godot tests/logic_test.tscn
## Covers weather parity with the Java build, save schema 8 round trip, legacy save migration,
## condition checks and the full action list of every quest step resolving without unknown steps.

var fails := 0
var checks := 0


func ok(cond: bool, what: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("GAGAL: ", what)


func _ready() -> void:
	# 1. weather parity (string from the Java WorldClock for days 1..400, first letter)
	var expect := FileAccess.get_file_as_string("res://tests/weather_reference.txt").strip_edges()
	var got := ""
	for d in range(1, 401):
		got += WorldClock.weather(d)[0]
	ok(got == expect, "cuaca harian sama dengan versi Java")
	# 2. save round trip
	var p := Progress.new_game("arland", 2, Data.first_step, Data.area("arland_room"))
	p.add_flag("A"); p.add_flag("B"); p.items.append("bunga"); p.add_count("surat", 3); p.coins = 99
	p.add_history("Arland", "senang", "Halo", "plaza", 1)
	p.snapshot("PRO")
	var json := JSON.stringify(p.to_dict(true))
	var q := Progress.from_dict(JSON.parse_string(json))
	ok(q != null, "save bisa dibaca ulang")
	ok(q.to_dict(true).hash() == JSON.parse_string(json).hash() or JSON.stringify(q.to_dict(true)) == json, "save identik setelah round trip")
	ok(q.slot == 2 and q.coins == 99 and q.count("surat") == 3 and q.has_flag("B") and q.dialogue_history.size() == 1, "isi save utuh")
	ok(int(p.to_dict(false).schema) == 8, "schema 8")
	# 3. legacy save (schema 1, layout v3) migrates position only
	var old := Progress.from_dict({"schema": 1, "route": "sofia", "step": "PRO_PHONE", "area": "sofia_room", "x": 480, "y": 320})
	ok(old != null and is_equal_approx(old.x, 300.0) and is_equal_approx(old.y, 224.0) and old.coins == 12, "migrasi save lama")
	ok(Progress.from_dict({"schema": 9, "route": "sofia", "step": "x", "x": 1, "y": 1}) == null, "schema terlalu baru ditolak")
	ok(Progress.from_dict({"schema": 8, "route": "budi", "step": "x", "x": 1, "y": 1}) == null, "route tidak valid ditolak")
	# 4. conditions
	var e := QuestEngine.new(Progress.new_game("sofia", 1, Data.first_step, Data.area("sofia_room")))
	e.p.add_flag("X_SOFIA")
	ok(e.check({"flags": ["X_$RU"]}), "token $RU")
	ok(not e.check({"notFlags": ["X_SOFIA"]}), "notFlags")
	ok(e.check({"countBelow": {"k": 1}}) and not e.check({"count": {"k": 1}}), "count / countBelow")
	ok(e.check({"chapters": ["PRO"]}) and not e.check({"minChapter": "C01"}), "chapter")
	# 5. every step target in the data exists
	var missing := 0
	var walk := func(self_ref, v):
		if v is Dictionary:
			if v.get("do") == "step" and Data.step(str(v.get("id", ""))).is_empty():
				missing += 1
			for k in v:
				self_ref.call(self_ref, v[k])
		elif v is Array:
			for x in v:
				self_ref.call(self_ref, x)
	walk.call(walk, Data.quests)
	ok(missing == 0, "semua aksi step menunjuk step yang ada")
	# 6. every scene referenced by an action exists
	var scenes_missing := []
	var walk2 := func(self_ref, v):
		if v is Dictionary:
			if v.get("do") == "scene":
				var id: String = Routes.resolve(str(v.get("id", "")), "arland")
				var id2: String = Routes.resolve(str(v.get("id", "")), "sofia")
				if Data.scene(id).is_empty() and Data.scene(id2).is_empty():
					scenes_missing.append(v.get("id"))
			for k in v:
				self_ref.call(self_ref, v[k])
		elif v is Array:
			for x in v:
				self_ref.call(self_ref, x)
	walk2.call(walk2, Data.quests)
	ok(scenes_missing.is_empty(), "semua adegan yang dipanggil ada: %s" % [scenes_missing.slice(0, 5)])
	# 7. save files are byte-compatible with the LibGDX SaveStore (CRC over Java compact JSON)
	var jr = SaveStore.unwrap_payload(FileAccess.get_file_as_string("res://tests/fixtures/save_schema8_v6.json"))
	ok(jr is Dictionary, "save buatan versi Java terbaca (CRC cocok): %s" % [jr if jr is String else "ok"])
	if jr is Dictionary:
		var jp := Progress.from_dict(jr)
		ok(jp != null and jp.step == "PRO_BOOK" and jp.coins == 40 and jp.has_flag("Ünicode \"kutip\"\n") and jp.dialogue_history.size() == 1, "isi save Java utuh")
		var out := OS.get_environment("SAVE_COMPAT_OUT")
		if out != "" and jp != null:
			var f: FileAccess = FileAccess.open(out, FileAccess.WRITE)
			f.store_string(SaveStore.wrap_payload(jp.to_dict(true)))
			f.close()
	# 8. slot save/load through user://
	var sp := Progress.new_game("sofia", 2, Data.first_step, Data.area("sofia_room"))
	sp.add_flag("T1")
	ok(SaveStore.save_slot(sp), "simpan slot")
	sp.add_flag("T2")
	ok(SaveStore.save_slot(sp), "simpan slot kedua kali (buat .bak)")
	var ld: Dictionary = SaveStore.load_slot("sofia", 2)
	ok(ld.status == "OK" and ld.value.has_flag("T2"), "muat slot")
	FileAccess.open(SaveStore.slot_path("sofia", 2), FileAccess.WRITE).store_string("rusak")
	ld = SaveStore.load_slot("sofia", 2)
	ok(ld.status == "RECOVERED" and ld.value.has_flag("T1"), "pulih dari .bak saat file utama rusak")
	SaveStore.delete_slot("sofia", 2)
	ok(SaveStore.load_slot("sofia", 2).status == "MISSING", "hapus slot")
	# 9. minigames: every config builds, and a correct play of the puzzle-like ones wins
	var mgs: Dictionary = Data.quests.get("minigames", {})
	var built := 0
	for id in mgs:
		for r in ["arland", "sofia"]:
			var g := Games.create(str(mgs[id].get("type", id)))
			g.init(mgs[id], r)
			g.x = 0; g.y = 0; g.w = 900; g.h = 480
			for k in 200:
				g.update(0.05)
				if k % 7 == 0:
					g.tap(450, 200)
			built += 1
	ok(built == mgs.size() * 2, "semua %d konfigurasi minigame jalan tanpa error" % mgs.size())
	var cl := Games.create("code"); cl.init(mgs.code_gua, "sofia")
	for i in cl.answer.size():
		cl.dial[i] = cl.answer[i]
	cl.check(); for k in 30: cl.update(0.05)
	ok(cl.finished and cl.score == 1, "peti kata sandi terbuka dengan jawaban benar")
	var ec := Games.create("v49_echo"); ec.init(mgs.v49_echo_plaza, "arland")
	for k in 100: ec.update(0.1)
	for st in ec.patterns.duplicate():
		for b in st: ec.choose(b)
		for k in 100: ec.update(0.1)
	ok(ec.finished and ec.score == 5, "gema kenangan selesai tanpa salah = skor 5")
	var bq := Games.create("bouquet"); bq.init({}, "sofia")
	bq.chosen = bq.pattern.duplicate(); bq.submit()
	ok(bq.finished and bq.score == 4, "buket cocok")
	# 10. puzzle: wrong resets, hint after 2 fails, right order solves
	var po := PuzzleOverlay.new()
	add_child(po)
	var solved := []
	po.open(Data.quests.puzzles.C01_SYMBOLS, "sofia", true, func(ok): solved.append(ok))
	ok(po.input("BUNGA") == "WRONG" and po.input("BUKU") == "WRONG" and po.hint_visible(), "puzzle: salah 2x memunculkan petunjuk")
	ok(po.input("BINTANG") == "CORRECT" and po.input("BUKU") == "CORRECT" and po.input("BUNGA") == "SOLVED", "puzzle: urutan route Sofia benar")
	# 11. shop purchase through the engine
	var se := QuestEngine.new(Progress.new_game("arland", 3, Data.first_step, Data.area("arland_room")), true)
	se.p.coins = 15
	ok(se.purchase("senja", "kopi_senja").begins_with("Membeli") and se.p.coins == 3 and se.p.has_item("kopi_senja"), "toko: beli kopi")
	ok(se.purchase("senja", "kukis_madu").begins_with("Koin belum cukup") and se.purchase("senja", "kopi_senja").begins_with("Barang ini sudah"), "toko: koin kurang / sudah dimiliki")
	# 12. achievements and memory book states
	var ap := Progress.new_game("sofia", 3, Data.first_step, Data.area("sofia_room"))
	ap.play_seconds = 130; ap.chapters["PRO"] = true; ap.affection = 80
	var gd := {"completed": {"arland": ["C06"], "sofia": ["C06"]}, "achievements": ["start"]}
	var ach_added := Achievements.unlock(ap, gd)
	ok(ach_added == ["chapter", "heart", "both"] and gd.achievements.size() == 4, "prestasi: hanya yang baru, tidak dicabut")
	var mbk := MemoryBook.new()
	mbk.p = ap
	mbk.g = {"routeFlags": {"arland": ["A_FLAG"]}}
	ap.add_flag("S_FLAG")
	ok(mbk.entry_state({"route": "shared", "unlock": "S_FLAG"}) == "UNLOCKED"
		and mbk.entry_state({"route": "arland", "unlock": "A_FLAG"}) == "OTHER_SIDE"
		and mbk.entry_state({"route": "arland", "unlock": "NOPE"}) == "LOCKED"
		and mbk.entry_state({"route": "sofia", "unlock": "NOPE"}) == "LOCKED", "memory book: terbuka / sisi lain / terkunci")
	mbk.free()
	# 13. romance rules
	var rp := Progress.new_game("sofia", 3, Data.first_step, Data.area("sofia_room"))
	for st in Data.steps:
		if str(Data.step(st).get("chapter", "")) == "C02":
			rp.step = st
			break
	rp.companion = true; rp.coins = 40; rp.minute = 9 * 60; rp.items.append("kopi_senja")
	var re := QuestEngine.new(rp, false)
	ok(re.romance_ready(), "romansa siap di Chapter 2 bersama pasangan")
	ok(re.give_gift("kopi_senja").begins_with("Hadiah diberikan!") and not rp.has_item("kopi_senja") and rp.affection == 4, "hadiah: item dipakai, +4 kedekatan")
	ok(re.give_gift("kopi_senja").begins_with("Kamu sudah memberi"), "hadiah: satu per hari")
	ok(re.date_block("taman", "plaza").begins_with("Datang dahulu") and re.start_date("taman", "taman_kota").begins_with("Kencan dimulai!") and rp.coins == 32, "kencan: lokasi dicek, koin dipotong")
	ok(re.start_couple_action("gandengan", "plaza").begins_with("Aksi berdua!") and rp.holding_hands
		and re.start_couple_action("gandengan", "plaza") == "Berhenti bergandengan." and re.start_couple_action("gandengan", "plaza") == "Bergandengan lagi.", "gandengan: aktif / lepas / lagi tanpa bonus ganda")
	ok(re.couple_action_actions("pelukan").size() >= 2 and re.date_actions("taman").size() >= 3, "aksi romansa menghasilkan cutscene + scene")
	# 14. soundscape choice (same rules as SoundscapePlan.java)
	ok(Soundscape.music_for("plaza", "town", "rain", false, 13 * 60) == "rain_lullaby" and Soundscape.music_for("plaza", "town", "cerah", false, 21 * 60) == "city_night"
		and Soundscape.music_for("plaza", "town", "cerah", false, 17 * 60) == "city_evening" and Soundscape.music_for("cafe", "cafe", "rain", true, 600, "cinema_quiet") == "cinema_quiet", "musik per tempat, cuaca, jam, dan override cerita")
	ok(Soundscape.ambience_for("cafe", "rain", true, 600) == "rain_window" and Soundscape.ambience_for("taman_kota", "cerah", false, 21 * 60) == "night_crickets"
		and Soundscape.ambience_for("sofia_room", "cerah", true, 600) == "" and Soundscape.footstep_for("cafe") == "step_wood", "ambience dan langkah kaki")
	# 15. layered area soundscape (assets/audio/area_sound.json)
	var snd_cfg = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/area_sound.json"))
	var snd_miss := []
	for snd_aid in Data.maps:
		var snd_prof: Dictionary = snd_cfg.areas.get(snd_aid, {})
		if snd_prof.get("layers", []).is_empty():
			snd_miss.append(snd_aid + ":tanpa lapisan")
		for snd_l in snd_prof.get("layers", []):
			if not ResourceLoader.exists("res://assets/audio/amb/%s.ogg" % snd_l.id): snd_miss.append(snd_l.id)
		for snd_sp in snd_prof.get("spots", []):
			for snd_v in int(snd_cfg.spot_variants):
				if not ResourceLoader.exists("res://assets/audio/spots/%s_%d.ogg" % [snd_sp.id, snd_v + 1]): snd_miss.append(snd_sp.id)
		for snd_k in ["flow", "lake"]:
			if snd_prof.has(snd_k) and not ResourceLoader.exists("res://assets/audio/amb/%s.ogg" % snd_prof[snd_k].id): snd_miss.append(snd_prof[snd_k].id)
		if not snd_cfg.reverb.has(str(snd_prof.get("reverb", ""))): snd_miss.append(snd_aid + ":gema")
	for snd_e in snd_cfg.emitters.values():
		if not ResourceLoader.exists("res://assets/audio/amb/%s.ogg" % snd_e.id): snd_miss.append(snd_e.id)
	ok(snd_miss.is_empty(), "semua %d area punya suara berlapis & semua file ada %s" % [Data.maps.size(), snd_miss])
	var snd_day := AreaSound.layer_targets(snd_cfg.areas.plaza, AreaSound.tokens_for("cerah", 10 * 60))
	var snd_night := AreaSound.layer_targets(snd_cfg.areas.plaza, AreaSound.tokens_for("cerah", 22 * 60))
	var snd_wet := AreaSound.layer_targets(snd_cfg.areas.hutan_bisik, AreaSound.tokens_for("hujan", 10 * 60))
	ok(snd_day.has("birds_town") and not snd_day.has("crickets") and snd_night.has("crickets") and not snd_night.has("birds_town") and snd_night.city_crowd < snd_day.city_crowd
		and snd_wet.has("rain_leaves") and not snd_wet.has("birds_forest") and AreaSound.tokens_for("berangin", 600).wind, "lapisan suara ikut jam & cuaca")
	var snd_em := {"points": [[Vector2(100, 100), 400.0, 1.0]], "rects": [[Rect2(0, 900, 1000, 100), 300.0, 0.8]]}
	ok(AreaSound.emitter_gain(snd_em, Vector2(120, 100)).x > AreaSound.emitter_gain(snd_em, Vector2(400, 100)).x and AreaSound.emitter_gain(snd_em, Vector2(500, 500)).x == 0.0
		and AreaSound.emitter_gain(snd_em, Vector2(500, 950)).x > 0.7, "air mancur/sungai makin keras saat didekati")
	ok(Soundscape.music_for("dermaga", "town", "cerah", false, 600) == "harbor_day" and Soundscape.music_for("rumah_sari", "home_evening", "cerah", true, 600) == "grandma_house"
		and ResourceLoader.exists("res://assets/audio/music/street_stroll.ogg") and ResourceLoader.exists("res://assets/audio/music/gallery_light.ogg"), "lagu baru per area")
	# 16. V8 height layer (assets/data/elevation.json, src/logic/elevation.gd)
	var ev_pz: Dictionary = Data.area("plaza")
	ok(Elevation.at(ev_pz, 1200, 300) == 30.0 and Elevation.at(ev_pz, 1200, 700) == 0.0 and absf(Elevation.at(ev_pz, 1060, 451) - 15.0) < 0.6,
		"plaza: taman utara 30, jalan 0, tengah tangga st1 ~15")
	ok(Elevation.at(ev_pz, 1900, 900) == 34.0 and absf(Elevation.at(ev_pz, 1671, 918) - 17.0) < 1.0 and absf(Elevation.at(ev_pz, 2149, 918) - 17.0) < 1.0 and Elevation.at(ev_pz, 2166, 918) < 3.0,
		"plaza: teras kafe 34, tangga samping naik/turun ke arah yang benar")
	ok(Elevation.on_stairs(ev_pz, 1060, 451) and not Elevation.on_stairs(ev_pz, 1200, 700), "deteksi berdiri di tangga")
	var ev_bad := []
	var ev_cfg = JSON.parse_string(FileAccess.get_file_as_string("res://assets/data/elevation.json"))
	for ev_aid in Data.maps:
		var ev_a: Dictionary = Data.maps[ev_aid]
		for ev_s in ev_a.get("stairs", []):
			if not ev_cfg.areas.has(ev_aid):
				ev_bad.append("%s tanpa lapisan tinggi" % ev_aid); break
			var r: Array = ev_s.rect
			var lo_hi: Array = [Elevation.at(ev_a, r[0] + r[2] / 2.0, r[1] - 6), Elevation.at(ev_a, r[0] + r[2] / 2.0, r[1] + r[3] + 6)] if ev_s.get("dir", "down") in ["down", "up"] \
				else [Elevation.at(ev_a, r[0] - 6, r[1] + r[3] / 2.0), Elevation.at(ev_a, r[0] + r[2] + 6, r[1] + r[3] / 2.0)]
			if absf(lo_hi[0] - lo_hi[1]) < 4.0 or not Elevation.on_stairs(ev_a, r[0] + r[2] / 2.0, r[1] + r[3] / 2.0):
				ev_bad.append("%s/%s" % [ev_aid, ev_s.id])
	ok(ev_bad.is_empty(), "setiap tangga menghubungkan dua ketinggian berbeda %s" % [ev_bad])
	var ev_xs := Elevation.breaks(ev_pz, 0, 1024, Elevation.AXIS_X, 32.0)
	ok(ev_xs.has(196.0) and ev_xs.has(256.0) and ev_xs[0] == 0.0 and ev_xs[-1] == 1024.0, "grid tanah punya garis di tepi tangga")
	ok(Elevation.at(Data.area("cafe"), 400, 300) == 0.0 and not Elevation.has_any(Data.area("cafe")), "interior tetap datar")
	# 17. V8 settings (user://settings.json, src/logic/game_settings.gd)
	var gs := GameSettings.sanitize({"quality": "ultra", "fps": 30, "music": 2.0, "hud_scale": "besar", "left_hand": true, "x": 1})
	ok(gs.quality == "ultra" and gs.fps == 30 and gs.music == 1.0 and gs.hud_scale == 1.0 and gs.left_hand and not gs.has("x"), "pengaturan dibersihkan & dibatasi")
	ok(GameSettings.sanitize({"quality": "mega", "fps": 144}).quality == "high" and GameSettings.sanitize({"fps": 144}).fps == 60, "nilai tak dikenal kembali ke bawaan")
	var gs_keep: Dictionary = GameSettings.get_all().duplicate()
	GameSettings.set_value("quality", "low")
	GameSettings.load_file()
	ok(GameSettings.value("quality") == "low" and GameSettings.quality().shadows == false and GameSettings.quality().post == false, "preset Rendah tersimpan & mematikan bayangan/efek layar")
	GameSettings.set_value("fps", 30)
	ok(Engine.max_fps == 30, "frame rate 30 diterapkan")
	var gs_f := FileAccess.open(GameSettings.PATH, FileAccess.WRITE); gs_f.store_string("{rusak"); gs_f.close()
	GameSettings.load_file()
	ok(GameSettings.value("quality") == "high", "file pengaturan rusak -> bawaan, tanpa crash")
	GameSettings.current = gs_keep; GameSettings.save_file(); GameSettings.apply_global()
	# 18. V8 Living NPC routing + Weather 3.0
	ok(World.first_hop("plaza", "perumahan") == "jalan_kota" and World.first_hop("cafe", "taman_kota") == "plaza"
		and World.first_hop("plaza", "plaza") == "" and World.first_hop("plaza", "tidak_ada") == "", "NPC memilih pintu di rute terpendek")
	var wx_storm := 0
	var wx_rain := 0
	for wx_d in range(1, 120):
		if WorldClock.weather(wx_d) == WorldClock.HUJAN:
			wx_rain += 1
			if WorldClock.storm(wx_d): wx_storm += 1
		elif WorldClock.storm(wx_d):
			wx_storm = -999
	ok(wx_rain > 0 and wx_storm > 0 and wx_storm < wx_rain, "badai hanya di sebagian hari hujan (%d dari %d)" % [wx_storm, wx_rain])
	ok(GameSettings.sanitize({"lightning": false}).lightning == false and GameSettings.sanitize({}).lightning == true, "opsi kilat petir")
	ok(ResourceLoader.exists("res://assets/audio/sfx/thunder.wav") and ResourceLoader.exists("res://assets/audio/sfx/step_stairs.wav"), "suara guntur & tangga ada")
	# 19. U3b characters and living NPCs (src/logic/acting.gd, src/game/npc_life.gd, tools/npc_memory_u3b.py)
	ok(Acting.pose_for("tertawa", true) == "senang" and Acting.pose_for("kaget", false) == "surprised"
		and Acting.pose_for("neutral", true) == "" and Acting.pose_for("tidak_ada", false) == "", "ekspresi dialog -> pose tubuh")
	var u_bad: Array = []
	for u_e in Acting.EIGHT:
		var u_p: String = Acting.EIGHT[u_e]
		if u_p != "" and not Actor.POSES.has(u_p):
			u_bad.append(u_p)
	ok(u_bad.is_empty() and Actor.POSES.find("senang") == 16 and Actor.POSES.find("kaget") == 20, "pose emosi ada di lembar pose %s" % [u_bad])
	for u_c in ["arland", "sofia"]:
		var u_ps: Texture2D = load("res://assets/characters/%s/poses_v53@2x.png" % u_c)
		var u_rs: Texture2D = load("res://assets/characters/%s/run_8dir_v53@2x.png" % u_c)
		ok(u_ps.get_height() / (Actor.FH * 2) >= Actor.POSES.size() and u_rs != null and u_rs.get_height() / (Actor.FH * 2) == 8,
			"%s: %d baris pose, siklus lari 8 arah" % [u_c, u_ps.get_height() / (Actor.FH * 2)])
	for u_k in {"hand_walk": 12, "hand_idle": 2, "hug": 2}:
		var u_t: Texture2D = load("res://assets/characters/couple/%s@2x.png" % u_k)
		ok(u_t != null and u_t.get_width() == Actor.CFW * 2 * {"hand_walk": 12, "hand_idle": 2, "hug": 2}[u_k] and u_t.get_height() == Actor.FH * 2 * 4,
			"lembar pasangan %s (4 arah)" % u_k)
	ok(NpcLife.pair_key("rini", "darmo") == "darmo|rini" and NpcLife.speaker_id(1, "a", "b") == "b" and NpcLife.speaker_id("darmo", "darmo", "rini") == "darmo",
		"kunci & pembicara obrolan NPC")
	var u_ch: Dictionary = Data._json("res://assets/data/npc_chatter.json")
	var u_ids := {}
	var u_npcs := {}
	for u_n in Data.quests.townNpcs:
		u_npcs[u_n.id] = u_n
	var u_cbad: Array = []
	for u_t2 in u_ch.get("generic", []):
		if u_ids.has(u_t2.id) or u_t2.lines.size() < 2: u_cbad.append(u_t2.id)
		u_ids[u_t2.id] = true
	for u_pk in u_ch.get("pairs", {}):
		var u_two: PackedStringArray = u_pk.split("|")
		if u_two.size() != 2 or u_two[0] >= u_two[1] or not u_npcs.has(u_two[0]) or not u_npcs.has(u_two[1]): u_cbad.append(u_pk)
		for u_t3 in u_ch.pairs[u_pk]:
			if u_ids.has(u_t3.id) or u_t3.lines.size() < 2: u_cbad.append(u_t3.id)
			u_ids[u_t3.id] = true
			for u_l in u_t3.lines:
				if not (str(u_l[0]) in u_two): u_cbad.append(u_t3.id + ":" + str(u_l[0]))
	ok(u_cbad.is_empty() and u_ids.size() >= 40, "%d obrolan NPC valid %s" % [u_ids.size(), u_cbad])
	var u_mem := 0
	var u_mbad: Array = []
	for u_n2 in Data.quests.townNpcs:
		var u_seen_mem := false
		for u_d in u_n2.get("dialogs", []):
			if str(u_d.get("id", "")).begins_with("MEM_"):
				u_mem += 1; u_seen_mem = true
				var u_f: String = u_d.when.flags[0]
				if not (u_d.when.notFlags as Array).has(u_d.id): u_mbad.append(u_d.id)
				if u_f.begins_with("SQ_") and not JSON.stringify(Data.quests.townNpcs).contains('"id":"%s"' % u_f) and not JSON.stringify(Data.quests).contains('"' + u_f + '"'):
					u_mbad.append(u_f)
			elif u_seen_mem:
				for u_a in u_d.get("actions", []):
					if u_a.get("do") in ["flag", "item", "removeItem", "count", "toast", "coins"] and not str(u_d.get("id", "")).begins_with("MEM_"):
						u_mbad.append("%s: dialog quest setelah ingatan" % u_n2.id)
	ok(u_mem == 19 and u_mbad.is_empty(), "NPC mengingat pilihan pemain: %d dialog sekali-tampil %s" % [u_mem, u_mbad])
	ok(ResourceLoader.exists("res://assets/fx/umbrella_0.png") and ResourceLoader.exists("res://assets/fx/umbrella_3.png"), "payung untuk hujan")
	var u_qe := QuestEngine.new(Progress.new_game("arland", 4, Data.first_step, Data.area("arland_room")))
	var u_mel: Dictionary = {}
	for u_n3 in Data.quests.townNpcs:
		if u_n3.id == "melati": u_mel = u_n3
	u_qe.p.minute = 10 * 60
	var u_before: Dictionary = u_qe.npc_dialog(u_mel)
	u_qe.p.add_flag("C02_RIBBON_LAVENDER")
	var u_after: Dictionary = u_qe.npc_dialog(u_mel)
	u_qe.p.add_flag("MEM_MELATI_LAVENDER")
	var u_later: Dictionary = u_qe.npc_dialog(u_mel)
	ok(u_before.get("id", "") != "MEM_MELATI_LAVENDER" and u_after.get("id", "") == "MEM_MELATI_LAVENDER" and u_later.get("id", "") != "MEM_MELATI_LAVENDER",
		"Bu Melati ingat pita lavender sekali, lalu kembali ke obrolan biasa")
	# 20. U2a 3D interiors (src/view3d/room_light.gd, src/view3d/furniture_volume.gd, tools/worldgen/rooms_hd.py)
	var w_noon := RoomLight.sky_at(12 * 60, false)
	var w_night := RoomLight.sky_at(0, false)
	var w_rain := RoomLight.sky_at(12 * 60, true)
	ok(w_noon.power > 0.8 and w_night.power <= 0.12 and w_night.stars > 0.5 and w_noon.stars < 0.05,
		"langit jendela: siang terang tanpa bintang, tengah malam hanya cahaya bulan dan bintang")
	ok(absf(w_rain.power - w_noon.power * 0.22) < 0.001 and w_rain.stars == 0.0 and w_rain.clouds == 1.0, "hujan meredupkan cahaya jendela dan menutup langit")
	var w_mono := true
	for w_m in range(0, 1440, 10):
		var w_a := RoomLight.sky_at(w_m, false); var w_b := RoomLight.sky_at(w_m + 10, false)
		if absf(w_b.power - w_a.power) > 0.2: w_mono = false
	ok(w_mono, "cahaya jendela berubah halus sepanjang hari (tanpa lompatan)")
	ok(RoomLight.skew_at(480) == 36.0 and RoomLight.skew_at(1080) == -36.0 and RoomLight.skew_at(780) == 0.0, "bercak matahari miring kanan pagi, kiri sore")
	var w_rooms := 0
	var w_wbad: Array = []
	for w_id in Data.maps:
		var w_ar: Dictionary = Data.maps[w_id]
		if not w_ar.get("room3d", false):
			continue
		for w_r in w_ar.get("windows", []):
			if w_r.size() != 4 or w_r[0] < 0 or w_r[0] + w_r[2] > w_ar.w or w_r[1] < 0 or w_r[1] + w_r[3] > 150 or w_r[2] < 30 or w_r[3] < 30:
				w_wbad.append("%s %s" % [w_id, w_r])
		if not w_ar.get("windows", []).is_empty(): w_rooms += 1
	ok(w_rooms == 7 and w_wbad.is_empty(), "%d ruangan berjendela hidup, kaca di dinding belakang %s" % [w_rooms, w_wbad])
	var w_missing: Array = []
	var w_vbad: Array = []
	var w_vols := 0
	for w_k in Data.props:
		if not str(w_k).begins_with("room_"):
			continue
		var w_d: Dictionary = Data.props[w_k]
		if not ResourceLoader.exists("res://assets/" + w_d.image): w_missing.append(w_k)
		if w_d.has("vol"):
			w_vols += 1
			var w_v: Array = w_d.vol
			var w_tex: Texture2D = load("res://assets/" + w_d.image)
			var w_tw := w_tex.get_width() * 0.5; var w_th := w_tex.get_height() * 0.5
			if w_v.size() != 5 or w_v[2] < 14 or w_v[4] < 12 or w_v[0] < -w_tw / 2 - 1 or w_v[0] + w_v[2] > w_tw / 2 + 1 or -w_v[1] > w_th + 1 or w_v[1] + w_v[3] + w_v[4] > 0.5:
				w_vbad.append("%s %s" % [w_k, w_v])
	ok(w_missing.is_empty(), "setiap perabot ruangan punya gambar (%d hilang) %s" % [w_missing.size(), w_missing.slice(0, 3)])
	ok(w_vols >= 120 and w_vbad.is_empty(), "%d perabot punya blok 3D di dalam sprite-nya %s" % [w_vols, w_vbad.slice(0, 3)])
	ok(FurnitureVolume.depth_for([-35, -101, 70, 8, 92], 200.0) == 21.0 and FurnitureVolume.depth_for([-35, -101, 70, 8, 92], 10.0) == 10.0
		and FurnitureVolume.depth_for([-48, -41, 96, 20, 20], 200.0) == 32.0 and FurnitureVolume.depth_for([-40, -20, 120, 30, 4], 200.0) == 34.0,
		"kedalaman blok: dari lukisan atasnya, minimal sepertiga lebar, dibatasi tinggi dan ruang ke dinding")
	var w_sv := WinStub.new()
	var w_q := FurnitureVolume.side_quad(w_sv, 100.0, Vector2(100, 300), 0.0, 92.0, 21.0)
	var w_ray := Vector3(0, -sin(WorldView3D.PITCH), -cos(WorldView3D.PITCH))
	var w_f1b1: Vector3 = (w_q[2] as Vector3) - (w_q[1] as Vector3)
	ok((w_q[0] as Vector3).is_equal_approx(w_sv.stand(100, 300, 0)) and (w_q[1] as Vector3).is_equal_approx(w_sv.stand(100, 300, 92))
		and w_f1b1.normalized().is_equal_approx(w_ray) and is_equal_approx((w_q[3] as Vector3).z, (w_q[0] as Vector3).z - 21.0 * WorldView3D.S)
		and (w_q[2] as Vector3).y > (w_q[3] as Vector3).y,
		"sisi 3D perabot menempel di bidang sprite dan atasnya searah sinar kamera (siluet tidak berubah)")
	# 21. U2b outdoor 3D (tools/extrude_u2b.py, src/view3d/prop_extrude.gd, world_mist.gd, world_particles.gd, tools/bridges_u2b.py)
	var x_n := 0
	var x_bad: Array = []
	var x_pic: Array = []
	var x_up := sin(WorldView3D.PITCH) / (cos(WorldView3D.TILT) * cos(WorldView3D.PITCH) - sin(WorldView3D.TILT) * sin(WorldView3D.PITCH))
	for x_k in Data.props:
		var x_d: Dictionary = Data.props[x_k]
		if not x_d.has("ext"):
			continue
		x_n += 1
		var x_pts: Array = x_d.ext.p
		var x_img := Image.load_from_file(ProjectSettings.globalize_path("res://assets/" + x_d.image))
		var x_k2 := Data.prop_scale(x_d)
		var x_w := x_img.get_width() * x_k2; var x_h := x_img.get_height() * x_k2
		var x_area := 0.0
		for x_i in x_pts.size():
			var x_a: Array = x_pts[x_i]; var x_b: Array = x_pts[(x_i + 1) % x_pts.size()]
			x_area += float(x_a[0]) * float(x_b[1]) - float(x_b[0]) * float(x_a[1])
			if absf(x_a[0]) > x_w / 2 + 1 or x_a[1] < -0.5 or x_a[1] > x_h + 0.5 or x_a[2] < 0.0 or x_a[2] > 1.0:
				x_bad.append(x_k)
			# from the gameplay camera the back of this point must land on the painting (within 1 px)
			var x_hu: float = x_a[1] + (1.0 - float(x_a[2])) * x_up * float(x_d.ext.d)
			var x_hit := false
			for x_dy in [-1.0, -0.5, 0.0, 0.5, 1.0]:
				for x_dx in [-1.0, -0.5, 0.0, 0.5, 1.0]:
					var x_c := int((float(x_a[0]) + x_dx + x_w / 2.0) / x_k2); var x_r := int((x_h - x_hu + x_dy) / x_k2)
					if x_c >= 0 and x_r >= 0 and x_c < x_img.get_width() and x_r < x_img.get_height() and x_img.get_pixel(x_c, x_r).a > 0.5:
						x_hit = true
			if not x_hit and not x_pic.has(x_k): x_pic.append(x_k)
		if x_pts.size() < 3 or x_area <= 0.0 or float(x_d.ext.d) < 4.0 or float(x_d.ext.d) > 48.0: x_bad.append(x_k)
	ok(x_n >= 80 and x_bad.is_empty(), "%d prop luar punya kontur 3D yang sah (berlawanan jarum jam, di dalam sprite) %s" % [x_n, x_bad.slice(0, 3)])
	ok(x_pic.is_empty(), "sisi 3D tidak mengubah gambar dari kamera permainan %s" % [x_pic.slice(0, 3)])
	ok(PropExtrude.back(10.0, 0.0).is_equal_approx(Vector3(0, 0, -10.0 * WorldView3D.S))
		and PropExtrude.back(10.0, 1.0).normalized().is_equal_approx(Vector3(0, -sin(WorldView3D.PITCH), -cos(WorldView3D.PITCH)))
		and is_equal_approx(PropExtrude.back(10.0, 1.0).z, -10.0 * WorldView3D.S), "dorongan ke belakang: lurus di tanah atau searah sinar kamera")
	ok(PropExtrude.triangles("hd_rock_a", 32, 22) > 6 and PropExtrude.triangles("hd_fence_picket", 98, 35) > 20 and not PropExtrude.has("hd_tree_oak_a") and not PropExtrude.has("hd_bush_a"),
		"batu dan pagar bervolume; pohon dan semak tidak")
	var x_pl: Array = Data.props.hd_planter_violet.ext.p
	var x_top := 0.0
	for x_q in x_pl: x_top = maxf(x_top, float(x_q[1]))
	ok(x_top < 20.0, "pot bunga hanya potnya yang bervolume, bukan tanamannya (puncak %.0f dari 36 px)" % x_top)
	ok(is_equal_approx(WorldMist.strength_at(360, "cerah"), 1.0) and WorldMist.strength_at(720, "cerah") == 0.0
		and WorldMist.strength_at(1200, "cerah") > 0.0 and WorldMist.strength_at(1200, "cerah") <= 0.3
		and is_equal_approx(WorldMist.strength_at(720, "rain"), 0.45) and is_equal_approx(WorldMist.strength_at(360, "berangin"), 0.4),
		"kabut: tebal saat subuh, hilang siang, tipis senja, ada saat hujan, menipis saat berangin")
	ok(WorldMist.colour_at(720, "rain").is_equal_approx(Color(0.72, 0.76, 0.82)) and WorldMist.colour_at(30, "cerah").b > WorldMist.colour_at(30, "cerah").r,
		"warna kabut: abu-abu saat hujan, kebiruan di malam hari")
	ok(WorldParticles.palette_for("hd_tree_cherry_a") == WorldParticles.PINK and WorldParticles.palette_for("hd_tree_autumn_b") == WorldParticles.ORANGE
		and WorldParticles.palette_for("hd_tree_oak_a") == WorldParticles.GREEN and WorldParticles.leaf_amount(5, 2400, 1600) == 0
		and WorldParticles.leaf_amount(863, 3200, 2400) == 40 and WorldParticles.leaf_amount(136, 2400, 1760) > 12,
		"daun gugur ikut warna pohonnya, jumlah ikut kerapatan pohon")
	var x_tk := Data.area("taman_kota"); var x_pz := Data.area("plaza")
	ok(Elevation.at(x_tk, 1450, 1450) == 4.0 and Elevation.at(x_tk, 1402, 1450) == 0.0 and Elevation.at(x_tk, 1398, 1450) == 0.0
		and is_equal_approx(Elevation.at(x_pz, 486, 1373), 6.0) and Elevation.at(x_pz, 486, 1323) == 0.0 and Elevation.at(x_pz, 1200, 1373) > 7.5,
		"jembatan punya tinggi: dek Taman Kota naik, jembatan kanal Plaza melengkung")
	var x_posts := 0
	for x_pp in x_tk.props + x_pz.props:
		if (x_pp.type == "hd_fence_h" and x_pp.x == 1450) or ((x_pp.type == "hd_pier_post" or x_pp.type == "hd_bollard") and x_pp.y in [1332.0, 1420.0]): x_posts += 1
	ok(x_posts == 14, "pagar dan tiang jembatan terpasang (%d dari 14)" % x_posts)
	# 22. U2c dream maps (tools/worldgen/dream_hd.py themes, world_particles.gd / world_mist.gd presets, tools/lantern_unlit_u2c.py)
	var c_need := {"lantern_field": ["hd_stall_red", "hd_stall_blue", "hd_lantern_string", "hd_bunting"], "star_path": ["hd_observatory", "hd_log_bench"],
		"starfall_village": ["hd_stall_blue", "hd_lantern_string"], "eternal_garden": ["hd_fountain_tiered", "hd_pergola", "hd_swing"], "moonlight_lake": ["hd_bench", "hd_lily_a"]}
	var c_miss: Array = []
	for c_a in c_need:
		var c_types := {}
		for c_p in Data.area(c_a).props: c_types[c_p.type] = true
		for c_t in c_need[c_a]:
			if not c_types.has(c_t): c_miss.append("%s:%s" % [c_a, c_t])
	ok(c_miss.is_empty(), "landmark khas tiap map mimpi terpasang %s" % [c_miss])
	ok(WorldParticles.DREAM.size() == 6 and WorldParticles.DREAM.lantern_field.sky_lanterns > 0 and WorldParticles.DREAM.starfall_village.smoke
		and WorldParticles.DREAM.gua_kristal.has("motes") and WorldMist.DREAM.moonlight_lake[0] > 0.5, "efek khas: lentera terbang, asap cerobong, debu kristal, kabut danau")
	var c_low: Array = []
	for c_a in ["star_path", "starfall_village", "eternal_garden", "moonlight_lake", "lantern_field", "gua_kristal"]:
		for c_p in Data.area(c_a).props:
			var c_d: Dictionary = Data.props.get(c_p.type, {})
			if not str(c_d.get("image", "@2x")).contains("@2x") and not c_low.has(c_p.type): c_low.append(c_p.type)
			if c_p.has("alt") and not str(Data.props.get(c_p.alt, {}).get("image", "@2x")).contains("@2x") and not c_low.has(c_p.alt): c_low.append(c_p.alt)
	ok(c_low.is_empty() and not str(Data.props.lantern_off.image).contains("lantern_post"), "map mimpi tanpa sprite 1x; lentera padam tidak ikut menyala %s" % [c_low])
	ok(ResourceLoader.exists("res://assets/props/lantern_off.png") and ResourceLoader.exists("res://assets/props/lantern_post.png"), "file lentera lama tetap ada untuk minigame")
	# 23. U5c story clarity (tools/story_u5c.py): rules said once, recaps, Indonesian place names, glossary
	var u_rules := 0
	for u_l in Data.scene("P-X02").get("lines", []):
		if u_l.get("u5c", false): u_rules += 1
	var u_lumi := ""
	for u_l in Data.scene("C04-X02").get("lines", []):
		if u_l.get("u5c", false): u_lumi += str(u_l.t)
	ok(u_rules == 3 and u_lumi.contains("menjaga buku") and u_lumi.contains("The Quiet"), "aturan dunia dijelaskan di Prolog, peran Lumi dan arti The Quiet di Bab 4")
	var u_norecap: Array = []
	for u_c in ["C01", "C02", "C03", "C04", "C05", "C06", "EPI"]:
		if Data.chapter_recap(u_c).length() < 60: u_norecap.append(u_c)
	ok(u_norecap.is_empty() and Data.chapter_recap("PRO") == "", "setiap bab punya ringkasan 'Sebelumnya' %s" % [u_norecap])
	var u_en: Array = []
	for u_a in ["memory_garden", "lantern_field", "star_path", "starfall_village", "eternal_garden", "rain_garden", "clockwork_station", "moonlight_lake", "memory_bridge", "hall_of_tomorrow"]:
		var u_n := str(Data.maps[u_a].get("name", ""))
		if not (u_n.begins_with("Taman") or u_n.begins_with("Padang") or u_n.begins_with("Jalan") or u_n.begins_with("Desa") or u_n.begins_with("Stasiun") or u_n.begins_with("Danau") or u_n.begins_with("Jembatan") or u_n.begins_with("Balai")):
			u_en.append(u_n)
	ok(u_en.is_empty(), "nama tempat mimpi berbahasa Indonesia %s" % [u_en])
	var u_gl: Array = Data.memory_book.get("glossary", [])
	var u_glbad := 0
	for u_g in u_gl:
		if Data.chapter_index(str(u_g.chapter)) < 0 or str(u_g.text).length() < 30 or str(u_g.text).length() > 135: u_glbad += 1
	ok(u_gl.size() >= 9 and u_glbad == 0 and str(u_gl[0].chapter) == "PRO", "kamus istilah: %d istilah, terbuka per bab, muat 3 baris (≤135 huruf)" % u_gl.size())
	# 24. U5d one name per place: no old English dream-place name in any text a player reads
	var n_hits: Array = []
	for n_src in [Data.story, Data.quests, Data.memory_book, {"areas": Data.maps}]:
		_eng_names(n_src, "", n_hits)
	ok(n_hits.is_empty(), "nama tempat lama tidak tersisa di pintu, misi, dan dialog %s" % [n_hits.slice(0, 3)])
	ok(str(Data.memory_book.glossary[0].term).contains("Memory Book") and str(Data.scene("P-X02").lines.filter(func(l): return l.get("u5c", false))[0].t).contains("Memory Book, Buku Kenangan"), "Memory Book dan Buku Kenangan disebut sebagai satu benda")
	print("%s: %d pemeriksaan, %d gagal" % ["SEMUA LULUS" if fails == 0 else "ADA YANG GAGAL", checks, fails])
	get_tree().quit(1 if fails > 0 else 0)


## A stand-in for WorldView3D.stand() on flat ground (room3d rooms have no elevation).
class WinStub:
	func stand(x: float, y: float, h: float) -> Vector3:
		var t := WorldView3D.TILT
		return Vector3(x * WorldView3D.S, cos(t) * h * WorldView3D.S, y * WorldView3D.S + sin(t) * h * WorldView3D.S)


const OLD_PLACES := ["Starfall", "Lantern Field", "Star Path", "Eternal Garden", "Rain Garden", "Clockwork Station", "Moonlight Lake", "Memory Bridge", "Hall of Tomorrow", "Memory Garden"]
const SHOWN := ["t", "text", "sub", "label", "title", "desc", "hint", "arland", "sofia", "objective"]


func _eng_names(o, key: String, hits: Array) -> void:
	if o is Dictionary:
		for k in o:
			_eng_names(o[k], str(k), hits)
	elif o is Array:
		for v in o:
			_eng_names(v, key, hits)
	elif o is String and SHOWN.has(key):
		for n in OLD_PLACES:
			if o.contains(n):
				hits.append(o.left(60))
