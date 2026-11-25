shader_type canvas_item;
// 2.5D screen pass (cheap, no mipmaps): depth-of-field style blur at the top and bottom of the view
// (tilt-shift), soft bloom from bright pixels, colour grade (cool shadows, warm highlights), vignette.
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform float blur_amt = 1.0;
uniform float bloom = 0.22;
uniform float vignette = 0.32;
uniform float warmth = 0.0;      // + at golden hour
uniform bool taps = true;        // false on medium quality: grade + vignette only

void fragment() {
	vec2 uv = SCREEN_UV;
	vec3 col = texture(screen_tex, uv).rgb;
	float band = smoothstep(0.26, 0.0, uv.y) + 0.6 * smoothstep(0.84, 1.0, uv.y);
	float r = band * 3.2 * blur_amt;
	vec3 glow = vec3(0.0);
	vec2 px = SCREEN_PIXEL_SIZE;
	// 6 taps on a rotated ring: used for both the blur (radius r) and the bloom (radius 7)
	for (int i = 0; i < (taps ? 6 : 0); i++) {
		float a = float(i) * 1.0472 + 0.4;
		vec2 o = vec2(cos(a), sin(a));
		if (r > 0.05) {
			col += texture(screen_tex, uv + o * px * r).rgb;
		}
		glow += max(texture(screen_tex, uv + o * px * 7.0).rgb - vec3(0.74), vec3(0.0));
	}
	if (taps && r > 0.05) {
		col /= 7.0;
	}
	col += glow * (bloom * 0.8);
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	vec3 grade = mix(vec3(0.95, 0.98, 1.05), vec3(1.04 + warmth * 0.06, 1.0 + warmth * 0.01, 0.95 - warmth * 0.05), smoothstep(0.15, 0.85, l));
	col *= grade;
	vec2 d = (uv - 0.5) * vec2(1.0, 1.2);
	col *= 1.0 - dot(d, d) * vignette * 1.5;
	COLOR = vec4(col, 1.0);
}
