shader_type spatial;
// V8.10 water reflections: a sprite drawn upside down on the water plane below its foot, masked to
// the area's open water, wobbling with the surface and fading with distance from the foot.
// Used for standing props (MultiMesh per texture) and for characters (one quad each).
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform sampler2D mask_tex : filter_linear;
uniform vec2 map_size = vec2(2400.0, 1600.0);
uniform vec4 uv_rect = vec4(0.0, 0.0, 1.0, 1.0);   // characters: sprite-sheet region (x, y, w, h)
uniform float strength = 0.52;
uniform vec3 tint = vec3(1.0);
uniform vec3 water_col = vec3(0.16, 0.36, 0.52);

varying vec2 map_pos;

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	map_pos = vec2(w.x, w.z) * 32.0;          // metres -> map px (water lies at height 0)
}

void fragment() {
	vec2 uv = UV;
	// uv.y = 1 at the foot (sprite bottom), 0 at the far end of the reflection
	float far = 1.0 - uv.y;
	uv.x += (sin(uv.y * 34.0 + TIME * 1.6) * 0.006 + sin(uv.y * 87.0 - TIME * 2.7) * 0.003) * (0.4 + far * 1.6);
	vec4 c = texture(albedo_tex, uv_rect.xy + uv * uv_rect.zw);
	float m = texture(mask_tex, map_pos / map_size).r;
	float fade = mix(1.0, 0.12, far * far);
	float streak = 0.82 + 0.18 * sin(map_pos.y * 0.85 + TIME * 2.4);
	float a = c.a * m * strength * fade * streak;
	if (a < 0.01) {
		discard;
	}
	ALBEDO = mix(c.rgb, water_col, 0.32) * tint;
	ALPHA = a;
}
