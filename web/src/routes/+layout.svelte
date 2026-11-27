<script lang="ts">
	// Deliberately minimal: the cinematic scroll journey (Lenis smooth-scroll, GSAP
	// ScrollTrigger, the preloader) belongs only to the marketing page's pinned room
	// journey — see routes/(marketing)/+layout.svelte. App pages (dashboard, calendar,
	// documents, ...) use native scroll and calm, quick transitions, per DESIGN.md:
	// "quick and subtle for daily use; cinematic only on login and page transitions."
	import './layout.css';
	import favicon from '#lib/assets/favicon.svg';
	import SkipLink from '#lib/components/SkipLink.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>SynkAI — The AI Boardroom Copilot</title>
	<meta
		name="description"
		content="SynkAI is an AI boardroom copilot in development: agendas and briefs before a meeting, live insight during it, structured minutes and tracked action items after it — feeding straight into the next meeting."
	/>
</svelte:head>

<SkipLink />
<main id="main-content">
	{@render children()}
</main>
