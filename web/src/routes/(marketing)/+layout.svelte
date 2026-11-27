<script lang="ts">
	// The cinematic scroll journey — Lenis smooth-scroll, GSAP ScrollTrigger pins/
	// scrubs, the preloader — is scoped to the marketing page only, via this route
	// group. See DESIGN.md §4 and §6.
	import { onMount } from 'svelte';
	import { getReducedMotion } from '#lib/motion/reducedMotion.svelte.js';
	import { loadGsap } from '#lib/motion/registerGsap.js';
	import { initLenis } from '#lib/motion/lenis.js';
	import Preloader from '#lib/components/Preloader.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	onMount(() => {
		let cleanup: (() => void) | undefined;
		if (!getReducedMotion()) {
			void loadGsap().then(({ gsap, ScrollTrigger }) => {
				void initLenis(gsap).then((destroyLenis) => {
					cleanup = destroyLenis;
				});
				ScrollTrigger.defaults({ markers: false });
			});
		}

		return () => cleanup?.();
	});
</script>

<Preloader />
{@render children()}
