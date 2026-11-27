<script lang="ts">
	// The authenticated app shell: sidebar nav + a calm, quick (250ms) fade between
	// pages — no Lenis/GSAP here, per DESIGN.md's "quick and subtle for daily use."
	import { fade } from 'svelte/transition';
	import { page } from '$app/state';
	import AppSidebar from '#lib/components/app/AppSidebar.svelte';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();

	let mobileNavOpen = $state(false);
</script>

<div class="app-shell">
	<aside class="sidebar-rail" class:open={mobileNavOpen}>
		<AppSidebar user={data.user} />
	</aside>

	{#if mobileNavOpen}
		<button
			class="mobile-scrim"
			aria-label="Close navigation"
			onclick={() => (mobileNavOpen = false)}
		></button>
	{/if}

	<div class="app-main">
		<header class="mobile-topbar">
			<button
				class="hamburger"
				aria-label="Open navigation"
				aria-expanded={mobileNavOpen}
				onclick={() => (mobileNavOpen = !mobileNavOpen)}
			>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M3 6h18M3 12h18M3 18h18" />
				</svg>
			</button>
			<span class="label label-signal">SynkAI</span>
		</header>

		{#key page.url.pathname}
			<div class="page-transition" in:fade={{ duration: 250 }}>
				{@render children()}
			</div>
		{/key}
	</div>
</div>

<style>
	.app-shell {
		display: flex;
		min-height: 100vh;
		background: var(--color-obsidian);
	}

	.sidebar-rail {
		width: 240px;
		flex-shrink: 0;
	}

	.app-main {
		flex: 1;
		min-width: 0;
		padding: clamp(1.25rem, 3vw, 2.5rem);
	}

	.mobile-topbar {
		display: none;
	}

	.mobile-scrim {
		display: none;
	}

	.hamburger {
		background: none;
		border: none;
		color: var(--color-ivory);
		width: 28px;
		height: 28px;
	}

	.hamburger svg {
		width: 100%;
		height: 100%;
	}

	.page-transition {
		min-height: 1px;
	}

	@media (max-width: 880px) {
		.sidebar-rail {
			position: fixed;
			inset: 0 auto 0 0;
			z-index: 30;
			transform: translateX(-100%);
			transition: transform 0.25s ease;
			width: 260px;
		}

		.sidebar-rail.open {
			transform: translateX(0);
		}

		.mobile-scrim {
			position: fixed;
			inset: 0;
			z-index: 20;
			background: color-mix(in srgb, var(--color-obsidian) 70%, transparent);
			border: none;
		}

		.mobile-topbar {
			display: flex;
			align-items: center;
			gap: 1rem;
			margin-bottom: 1.5rem;
		}

		.app-main {
			padding: 1.25rem 1.1rem;
		}
	}
</style>
