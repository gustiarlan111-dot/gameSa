shader_type spatial;
// U2b morning mist: one sheet of drifting ground mist (src/view3d/world_mist.gd stacks three).
// The noise is sampled in world space on a grid of `pix` metres, so the mist keeps the pixel-art grain
// and stays put on the ground while the sheet itself follows the camera.
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 col = vec3(1.0, 0.97, 0.92);
uniform float strength = 0.0;            // 0..1 from the clock, weather and area
uniform float layer_a = 0.5;             // this sheet's share
uniform float pix = 0.0625;              // two map pixels
uniform vec2 wind = vec2(0.12, 0.03);    // metres per second
uniform float seed = 0.0;
uniform vec2 centre = vec2(0.0);         // the camera's focus on the ground (xz)
uniform float radius = 22.0;             // fade out toward the sheet's edge

varying vec3 wpos;

float h21(vec2 p) {
	p = fract(p * vec2(127.1, 311.7) + seed);
	p += dot(p, p + 34.23);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 g = floor(wpos.xz / pix) * pix;                 // pixel grid
	vec2 q = g - wind * TIME;
	float n = vnoise(q * 0.12) * 0.55 + vnoise(q * 0.35 + 7.0) * 0.3 + vnoise(q * 0.9 + 3.0) * 0.15;
	float a = smoothstep(0.5, 0.82, n);                  // wisps and banks, with clear ground between
	float edge = 1.0 - smoothstep(radius * 0.6, radius, length(g - centre));
	// flat per pixel cell (the grid above), no stipple: the sprites are filtered smooth (K7 open), and a
	// dithered mist read as screen noise next to them
	float alpha = a * strength * layer_a * edge;
	ALBEDO = col;
	ALPHA = clamp(alpha, 0.0, 0.45);
}
