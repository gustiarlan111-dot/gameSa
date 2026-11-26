shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
// V8 camera occlusion: a tree or tall prop standing between the camera and Arland/Sofia is drawn
// through a 4x4 ordered dither instead of solid, so the couple shows through it. Dithering keeps the
// prop in the opaque pass (no sorting issues, pixel-art look) and `fade` eases between 1 (solid) and
// ~0.35. Same wind sway as sway3d.gdshader so the faded tree keeps moving with its neighbours.
// The prop's shadow is drawn by a separate shadows-only copy, so it never flickers while fading.
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap;
uniform bool use_normal = false;
uniform float amp = 0.0;
uniform float speed = 1.1;
uniform float fade = 1.0;

void vertex() {
	if (amp > 0.0) {
		float h = clamp(VERTEX.y, 0.0, 1.0);
		vec3 o = MODEL_MATRIX[3].xyz;
		float ph = o.x * 0.35 + o.z * 0.22;
		float w = sin(TIME * speed + ph) * 0.7 + sin(TIME * speed * 2.3 + ph * 1.7) * 0.3;
		float gust = 0.65 + 0.35 * sin(TIME * 0.33 + o.x * 0.05);
		VERTEX.x += w * gust * amp * h * h / max(length(MODEL_MATRIX[0].xyz), 0.0001);
	}
}

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(p, 4.0));
	int i = q.x + q.y * 4;
	// 4x4 Bayer matrix / 16
	float m[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	return (m[i] + 0.5) / 16.0;
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	if (c.a < 0.5 || bayer4(floor(FRAGCOORD.xy / 2.0)) > fade) {
		discard;
	}
	ALBEDO = c.rgb;
	ROUGHNESS = 0.88;
	if (use_normal) {
		NORMAL_MAP = texture(normal_tex, UV).rgb;
		NORMAL_MAP_DEPTH = 0.7;
	}
}
