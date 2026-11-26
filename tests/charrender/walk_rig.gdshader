shader_type spatial;
render_mode unshaded, cull_disabled;
// V8.3 procedural walk "rig" for the rigless Arland/Sofia GLBs (vertex colours, model space, y up,
// front = +z, height ~2). Legs swing from the hip, arms swing opposite from the shoulder, the
// upper body breathes. Used only to render sprite sheets (tests/charrender/render_sheets.gd).
uniform float phase = 0.0;        // walk cycle angle (radians)
uniform float swing = 0.0;        // leg swing amplitude (radians)
uniform float arm = 0.0;          // arm swing amplitude (radians)
uniform float breathe = 0.0;      // -1..1
uniform float hip_y = 0.52;
uniform float shoulder_y = 0.95;
uniform float arm_x = 0.27;
// poses (radians): arms forward (around x) and out/up to the side (around z) per arm, upper-body bow,
// sitting (thighs forward, body lowered). "l"/"r" are the character's own left/right (+x / -x).
uniform float l_fwd = 0.0;
uniform float r_fwd = 0.0;
uniform float l_up = 0.0;
uniform float r_up = 0.0;
uniform float bow = 0.0;
uniform float sit = 0.0;

vec3 rot_yz(vec3 v, float a, float py, float pz) {
	vec2 p = vec2(v.y - py, v.z - pz);
	float c = cos(a), s = sin(a);
	return vec3(v.x, c * p.x - s * p.y + py, s * p.x + c * p.y + pz);
}

vec3 rot_xy(vec3 v, float a, float px, float py) {
	vec2 p = vec2(v.x - px, v.y - py);
	float c = cos(a), s = sin(a);
	return vec3(c * p.x - s * p.y + px, s * p.x + c * p.y + py, v.z);
}

void vertex() {
	vec3 v = VERTEX;
	vec3 v0 = VERTEX;
	float side = clamp(v.x / 0.07, -1.0, 1.0);                     // soft seam between the legs
	float legw = 1.0 - smoothstep(hip_y - 0.12, hip_y, v.y);
	v = rot_yz(v, sin(phase) * swing * side * legw, hip_y, 0.05);
	float aw = smoothstep(arm_x - 0.04, arm_x + 0.03, abs(v.x)) * smoothstep(hip_y, hip_y + 0.06, v.y)
		* (1.0 - smoothstep(shoulder_y - 0.08, shoulder_y, v.y));
	float aside = v.x < 0.0 ? 1.0 : -1.0;
	v = rot_yz(v, -sin(phase) * arm * aside * aw, shoulder_y, 0.03);
	// pose arms: weight from the rest shape (v0) so a raised arm stays one piece
	float aw0 = smoothstep(arm_x - 0.04, arm_x + 0.03, abs(v0.x)) * smoothstep(hip_y, hip_y + 0.06, v0.y)
		* (1.0 - smoothstep(shoulder_y - 0.08, shoulder_y, v0.y));
	if (v0.x > 0.0) {
		v = rot_yz(v, -l_fwd * aw0, shoulder_y, 0.03);
		v = rot_xy(v, l_up * aw0, arm_x, shoulder_y);
	} else {
		v = rot_yz(v, -r_fwd * aw0, shoulder_y, 0.03);
		v = rot_xy(v, -r_up * aw0, -arm_x, shoulder_y);
	}
	// bow: everything above the hip pitches forward
	float uw = smoothstep(hip_y - 0.04, hip_y + 0.08, v0.y);
	v = rot_yz(v, bow * uw, hip_y, 0.0);
	// sit: thighs swing forward 80°, the whole figure drops by the thigh length
	// sit: the knee bends back first, then the whole leg swings forward from the hip, so the
	// thighs lie flat and the shins hang down; the figure drops by the thigh length
	float lw = 1.0 - smoothstep(hip_y - 0.12, hip_y, v0.y);
	float shin = 1.0 - smoothstep(0.22, 0.28, v0.y);
	v = rot_yz(v, -sit * 1.4 * shin, 0.25, 0.05);
	v = rot_yz(v, sit * 1.4 * lw, hip_y, 0.05);
	v.y -= sit * 0.27;
	v.y += breathe * 0.012 * smoothstep(hip_y, shoulder_y + 0.2, v.y);
	v.y += abs(sin(phase)) * swing * 0.06 * step(0.001, swing);     // body rises between steps
	VERTEX = v;
}

void fragment() {
	ALBEDO = COLOR.rgb;
}
