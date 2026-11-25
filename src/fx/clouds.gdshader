shader_type canvas_item;
render_mode blend_mul;
// Soft cloud shadows drifting over the world (multiplied), anchored to world space.
uniform float strength = 0.0;
uniform vec2 uv_off = vec2(0.0);
uniform vec2 uv_scale = vec2(1.0);
uniform vec3 shade = vec3(0.70, 0.74, 0.84);

void fragment() {
	vec2 uv = UV * uv_scale + uv_off;
	float n = texture(TEXTURE, uv).r * 0.7 + texture(TEXTURE, uv * 2.1 + vec2(0.37, 0.11)).r * 0.3;
	float c = smoothstep(0.48, 0.72, n);
	COLOR = vec4(mix(vec3(1.0), shade, c * strength), 1.0);
}
