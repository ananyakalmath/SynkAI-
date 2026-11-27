// shared reactive flag for prefers-reduced-motion.
// every animated component branches on this rather than assuming JS/WebGL motion is safe.
//
// initialised at module load (not from an onMount) because Svelte fires child
// onMount callbacks before the root layout's — a component that checked this
// from its own onMount could run before the layout ever set the real value.
// module evaluation always happens first, so reading it here is race-free.

let reduced = $state(false);

if (typeof window !== 'undefined') {
	const query = window.matchMedia('(prefers-reduced-motion: reduce)');
	reduced = query.matches;
	query.addEventListener('change', (event) => {
		reduced = event.matches;
	});
}

export function getReducedMotion() {
	return reduced;
}
