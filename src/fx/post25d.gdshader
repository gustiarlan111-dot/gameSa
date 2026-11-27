shader_type canvas_item;
// 2.5D screen pass: depth-of-field style blur at the top and bottom of the view
// (tilt-shift), soft bloom from bright pixels, colour grade (cool shadows, warm highlights), vignette.
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform sampler2D screen_mip : hint_screen_texture, filter_linear_mipmap;
uniform float blur_amt = 1.0;
uniform float bloom = 0.22;
uniform float vignette = 0.32;
uniform float warmth = 0.0;      // + at golden hour
uniform bool taps = true;        // false on medium quality: grade + vignette only
// cutscene film look (0 in normal play)
uniform float film = 0.0;        // overall amount
uniform float focus_y = 0.55;    // screen height of the subject: sharp there, soft away from it
uniform float dof = 0.35;
uniform vec3 mood_col = vec3(1.0);
uniform float mood_a = 0.0;
uniform float mood_desat = 0.0;
uniform float t = 0.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec2 uv = SCREEN_UV;
	vec3 col = texture(screen_tex, uv).rgb;
	float band = smoothstep(0.26, 0.0, uv.y) + 0.6 * smoothstep(0.84, 1.0, uv.y);
	// film focus: everything away from the subject's band goes soft, like a shallow lens
	float fband = smoothstep(0.1, 0.42, abs(uv.y - focus_y)) * (0.6 + dof);
	band = mix(band, max(band * 0.6, fband), film);
	float r = band * 3.2 * blur_amt;
	vec3 glow = vec3(0.0);
	vec2 px = SCREEN_PIXEL_SIZE;
	// U1: the blur and the bloom read the screen's mipmaps (one tap each) instead of 12 taps
	if (taps) {
		if (r > 0.05) {
			col = mix(col, textureLod(screen_mip, uv, log2(max(r, 1.0)) + 0.5).rgb, smoothstep(0.05, 1.5, r));
		}
		glow = max(textureLod(screen_mip, uv, 2.8).rgb - vec3(0.74), vec3(0.0)) * 6.0;
	}
	col += glow * (bloom * 0.8);
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	vec3 grade = mix(vec3(0.95, 0.98, 1.05), vec3(1.04 + warmth * 0.06, 1.0 + warmth * 0.01, 0.95 - warmth * 0.05), smoothstep(0.15, 0.85, l));
	col *= grade;
	if (film > 0.001) {
		// lens fringe at the edges (two extra taps), filmic S-curve with teal shadows and warm
		// highlights, the scene's mood colour, and a fine moving grain
		vec2 ca = (uv - 0.5) * px * 5.0 * film;
		col.r = mix(col.r, texture(screen_tex, uv + ca).r, 0.6 * film);
		col.b = mix(col.b, texture(screen_tex, uv - ca).b, 0.6 * film);
		float l2 = dot(col, vec3(0.299, 0.587, 0.114));
		vec3 s_curve = col * col * (3.0 - 2.0 * col);
		vec3 tone = mix(vec3(0.9, 0.98, 1.06), vec3(1.07, 1.0, 0.9), smoothstep(0.2, 0.8, l2));
		col = mix(col, mix(col, s_curve, 0.35) * tone, film * 0.8);
		vec3 grey = vec3(dot(col, vec3(0.299, 0.587, 0.114)));
		col = mix(col, mix(col, grey, mood_desat) * mood_col, mood_a * film);
		float g = hash(floor(uv / px * 0.5) + floor(t * 24.0)) - 0.5;
		col += g * 0.045 * film;
	}
	vec2 d = (uv - 0.5) * vec2(1.0, 1.2);
	col *= 1.0 - dot(d, d) * (vignette + 0.35 * film) * 1.5;
	COLOR = vec4(col, 1.0);
}
