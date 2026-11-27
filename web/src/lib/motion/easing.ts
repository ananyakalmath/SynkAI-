// tiny, three.js-free math helpers shared by the camera path and the
// scroll-driven Svelte components — kept out of boardroom.ts so importing
// them never pulls three.js into a component's static bundle.

export function clamp01(x: number) {
	return Math.min(1, Math.max(0, x));
}

export function smoothstep(edge0: number, edge1: number, x: number) {
	const t = clamp01((x - edge0) / (edge1 - edge0));
	return t * t * (3 - 2 * t);
}
