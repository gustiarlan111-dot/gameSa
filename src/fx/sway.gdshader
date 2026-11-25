shader_type canvas_item;
// Wind sway for foliage props: the top of the sprite drifts sideways, the base stays planted.
// The phase comes from the world position so neighbouring trees do not move in lockstep.
uniform float amp = 3.0;
uniform float speed = 1.1;
void vertex() {
	float k = 1.0 - UV.y;
	float ph = MODEL_MATRIX[3].x * 0.011 + MODEL_MATRIX[3].y * 0.007;
	float w = sin(TIME * speed + ph) * 0.7 + sin(TIME * speed * 2.3 + ph * 1.7) * 0.3;
	VERTEX.x += w * amp * k * k;
}
