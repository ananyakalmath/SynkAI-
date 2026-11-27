// client-only gsap loader. gsap + its plugins touch window/document at
// registration time, so they are never imported at module scope — every
// caller awaits this from onMount, keeping gsap out of the SSR bundle and
// out of the initial client chunk.

let cached: Promise<{
	gsap: typeof import('gsap').gsap;
	ScrollTrigger: typeof import('gsap/ScrollTrigger').ScrollTrigger;
	SplitText: typeof import('gsap/SplitText').SplitText;
}> | null = null;

export function loadGsap() {
	if (!cached) {
		cached = Promise.all([
			import('gsap'),
			import('gsap/ScrollTrigger'),
			import('gsap/SplitText')
		]).then(([gsapModule, scrollTriggerModule, splitTextModule]) => {
			const { gsap } = gsapModule;
			const { ScrollTrigger } = scrollTriggerModule;
			const { SplitText } = splitTextModule;
			gsap.registerPlugin(ScrollTrigger, SplitText);
			return { gsap, ScrollTrigger, SplitText };
		});
	}
	return cached;
}
