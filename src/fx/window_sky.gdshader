shader_type spatial;
// U2a: the glass of an interior window shows the real sky: colours by the hour, drifting clouds,
// stars and the moon at night, a skyline at the bottom, rain running down the glass, lightning.
// Pixel-art look: everything is computed on the window's own 2-texel-per-map-px grid.
render_mode unshaded, cull_disabled, shadows_disabled;

uniform vec3 top = vec3(0.44, 0.70, 0.92);
uniform vec3 bot = vec3(0.81, 0.91, 0.96);
uniform vec3 cloud_col = vec3(1.0);
uniform vec3 land = vec3(0.55, 0.72, 0.55);
uniform float clouds = 0.5;
uniform float stars = 0.0;
uniform float moon = 0.0;
uniform float rain = 0.0;
uniform float flash = 0.0;
uniform float seed = 0.0;
uniform vec2 size = vec2(64.0, 46.0);          // glass size in map px
uniform vec3 frame_col = vec3(0.984, 0.953, 0.918);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7)) + seed * 17.13) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

void fragment() {
	vec2 px = floor(UV * size * 2.0);               // texel grid (2 texels per map px)
	vec2 uv = (px + 0.5) / (size * 2.0);
	vec3 c = mix(top, bot, smoothstep(0.0, 1.0, uv.y));
	// clouds drift slowly to the right
	vec2 cp = vec2(uv.x * size.x / 26.0 - TIME * 0.015, uv.y * size.y / 14.0);
	float n = vnoise(cp) * 0.6 + vnoise(cp * 2.3 + 7.0) * 0.4;
	float cl = smoothstep(0.52, 0.72, n) * clouds * (1.0 - smoothstep(0.55, 0.75, uv.y));
	c = mix(c, cloud_col, cl);
	// stars twinkle, a small moon in some windows
	float st = step(0.987, hash(px)) * stars * (0.6 + 0.4 * sin(TIME * 2.0 + hash(px + 3.0) * 30.0));
	c += vec3(st) * (1.0 - smoothstep(0.5, 0.7, uv.y));
	vec2 mc = vec2(0.72, 0.28);
	float md = length((uv - mc) * vec2(size.x / size.y, 1.0));
	c = mix(c, vec3(0.98, 0.95, 0.82), moon * (1.0 - smoothstep(0.075, 0.09, md)) * step(0.5, hash(vec2(seed))));
	// skyline: soft hills and a few roofs, coloured by the light of the hour
	float hill = 0.74 + 0.05 * sin(uv.x * 7.0 + seed) + 0.03 * sin(uv.x * 19.0 + seed * 2.0);
	float roof = step(0.6, hash(vec2(floor(uv.x * size.x / 9.0), seed))) * 0.07;
	if (uv.y > hill - roof) {
		c = land * (0.92 - 0.12 * step(hill, uv.y));
	}
	// rain: streaks running down the glass and a few drops
	float lane = floor(px.x / 3.0);
	float fall = fract(uv.y * 1.6 - TIME * (0.7 + hash(vec2(lane, 1.0)) * 0.6) + hash(vec2(lane, 2.0)));
	float streak = step(0.9, hash(vec2(lane, 3.0))) * smoothstep(0.75, 1.0, fall);
	float drop = step(0.993, hash(px + floor(TIME * 0.5)));
	c = mix(c, vec3(0.86, 0.9, 0.96), (streak * 0.5 + drop * 0.6) * rain);
	c = mix(c, vec3(0.92, 0.95, 1.0), flash * 0.85);
	// glass glint on the left, mullions in the middle (as painted before)
	c += vec3(0.12) * step(px.x, 8.0) * step(4.0, px.x) * step(px.y, size.y * 0.7) * (1.0 - rain);
	vec2 mid = size;                                 // centre lines, 2 map px wide
	if (abs(px.x - mid.x) < 2.0 || abs(px.y - mid.y) < 2.0) {
		c = frame_col;
	}
	ALBEDO = c;
}
