import type Lenis from 'lenis';

let instance: Lenis | null = null;

// sets up Lenis and ties its raf to gsap's ticker so ScrollTrigger and
// smooth scroll stay in lockstep. Call only client-side, only when motion
// is not reduced. Returns a cleanup function.
export async function initLenis(gsap: typeof import('gsap').gsap) {
	const { default: LenisCtor } = await import('lenis');

	instance = new LenisCtor({
		duration: 1.1,
		smoothWheel: true
	});

	const onTick = (time: number) => {
		instance?.raf(time * 1000);
	};
	gsap.ticker.add(onTick);
	gsap.ticker.lagSmoothing(0);

	return () => {
		gsap.ticker.remove(onTick);
		instance?.destroy();
		instance = null;
	};
}

export function getLenis() {
	return instance;
}
