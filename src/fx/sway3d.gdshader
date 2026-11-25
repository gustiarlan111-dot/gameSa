shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
// Wind sway for 3D foliage quads (trees, grass, reeds, bushes). The quad's local y runs 0 (foot)
// to 1 (top); the top drifts sideways while the base stays planted. Phase comes from the instance
// position so neighbours do not move in lockstep, and a slow gust swell varies the strength.
// The shadow pass runs the same vertex code, so shadows sway with the plant.
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap;
uniform bool use_normal = false;
uniform float amp = 0.12;       // world units at the top of the sprite
uniform float speed = 1.1;

void vertex() {
	float h = clamp(VERTEX.y, 0.0, 1.0);
	vec3 o = MODEL_MATRIX[3].xyz;
	float ph = o.x * 0.35 + o.z * 0.22;
	float w = sin(TIME * speed + ph) * 0.7 + sin(TIME * speed * 2.3 + ph * 1.7) * 0.3;
	float gust = 0.65 + 0.35 * sin(TIME * 0.33 + o.x * 0.05);
	VERTEX.x += w * gust * amp * h * h / max(length(MODEL_MATRIX[0].xyz), 0.0001);
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	ALBEDO = c.rgb;
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 0.88;
	if (use_normal) {
		NORMAL_MAP = texture(normal_tex, UV).rgb;
		NORMAL_MAP_DEPTH = 0.7;
	}
}
