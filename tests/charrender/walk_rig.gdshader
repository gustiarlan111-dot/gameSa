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
// V8.3b: walking legs read as two legs (pinch each toward its own axis, cut the fused crotch skin),
// the trailing knee bends, and only the outer arm/hand swings (the torso side stays put).
uniform float leg_gap = 0.022;     // half-gap opened between the legs (model units)
uniform float knee = 0.0;          // knee flex of the trailing leg (radians)
uniform float arm_outer = 0.305;   // |x| where the arm starts, outside the torso
varying float v_x0;
varying float v_y0;

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
	v_x0 = v0.x; v_y0 = v0.y;
	// two legs: below the crotch each half slides toward its own leg axis, opening a small gap
	float below = 1.0 - smoothstep(hip_y - 0.16, hip_y - 0.04, v0.y);
	float legside = v0.x < 0.0 ? -1.0 : 1.0;
	v.x += legside * leg_gap * below * (1.0 - smoothstep(0.0, 0.14, abs(v0.x)));
	float side = clamp(v0.x / 0.03, -1.0, 1.0);                    // sharp seam: legs move as two
	float legw = 1.0 - smoothstep(hip_y - 0.12, hip_y, v0.y);
	float a_leg = sin(phase) * swing * side;
	// trailing knee: a positive angle swings the foot back (front = +z); that leg bends below the knee
	float shin_w = 1.0 - smoothstep(0.2, 0.3, v0.y);
	float flex = knee * clamp(a_leg / max(swing, 0.001), 0.0, 1.0);
	v = rot_yz(v, flex * shin_w * step(0.001, swing), 0.25, 0.05);
	v = rot_yz(v, a_leg * legw, hip_y, 0.05);
	float aw = smoothstep(arm_outer - 0.02, arm_outer + 0.02, abs(v0.x)) * smoothstep(hip_y - 0.02, hip_y + 0.06, v0.y)
		* (1.0 - smoothstep(shoulder_y - 0.1, shoulder_y - 0.02, v0.y));
	float aside = v0.x < 0.0 ? 1.0 : -1.0;
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
	// skin stretched across the opened crotch gap (triangles joining the two legs) is not drawn
	if (leg_gap > 0.0 && abs(v_x0) < 0.012 && v_y0 < hip_y - 0.06) {
		discard;
	}
	ALBEDO = COLOR.rgb;
}
