<script lang="ts">
	import { onMount } from 'svelte';
	import { getReducedMotion } from '#lib/motion/reducedMotion.svelte.js';

	const SESSION_KEY = 'synkai-entered';
	const DURATION_MS = 1100;

	let visible = $state(false);
	let filled = $state(false);
	let count = $state(0);
	let dismissing = $state(false);
	let timer: ReturnType<typeof setInterval> | undefined;
	let dismissTimeout: ReturnType<typeof setTimeout> | undefined;

	function dismiss() {
		if (dismissing) return;
		dismissing = true;
		clearInterval(timer);
		clearTimeout(dismissTimeout);
		try {
			sessionStorage.setItem(SESSION_KEY, '1');
		} catch {
			// storage may be unavailable (private mode) — fine to skip remembering
		}
		setTimeout(() => {
			visible = false;
		}, 450);
	}

	onMount(() => {
		if (getReducedMotion()) return;

		let alreadyEntered: boolean;
		try {
			alreadyEntered = sessionStorage.getItem(SESSION_KEY) === '1';
		} catch {
			alreadyEntered = false;
		}
		if (alreadyEntered) return;

		visible = true;
		requestAnimationFrame(() => {
			filled = true;
		});

		const steps = 40;
		const stepTime = DURATION_MS / steps;
		let tick = 0;
		timer = setInterval(() => {
			tick += 1;
			count = Math.min(100, Math.round((tick / steps) * 100));
			if (tick >= steps) clearInterval(timer);
		}, stepTime);

		dismissTimeout = setTimeout(dismiss, DURATION_MS + 350);

		return () => {
			clearInterval(timer);
			clearTimeout(dismissTimeout);
		};
	});
</script>

<svelte:window onkeydown={() => visible && dismiss()} />

{#if visible}
	<button
		type="button"
		class="preloader"
		class:dismissing
		aria-label="entering the boardroom — skip intro"
		onclick={dismiss}
	>
		<span class="preloader-label" aria-live="polite">entering the boardroom</span>
		<span class="preloader-line">
			<span class="preloader-fill" class:filled></span>
		</span>
		<span class="preloader-count">{count.toString().padStart(2, '0')}</span>
		<span class="preloader-skip">tap or press any key to skip</span>
	</button>
{/if}

<style>
	.preloader {
		position: fixed;
		inset: 0;
		z-index: 300;
		background: var(--color-obsidian);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.25rem;
		transition: opacity 0.45s ease;
		border: none;
		width: 100%;
		margin: 0;
	}

	.preloader.dismissing {
		opacity: 0;
	}

	.preloader-label {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: var(--color-ivory-dim);
	}

	.preloader-line {
		width: min(220px, 60vw);
		height: 1px;
		background: var(--color-graphite-2);
		overflow: hidden;
	}

	.preloader-fill {
		display: block;
		height: 100%;
		width: 100%;
		background: var(--color-brass);
		transform: scaleX(0);
		transform-origin: left;
		transition: transform 1.1s linear;
	}

	.preloader-fill.filled {
		transform: scaleX(1);
	}

	.preloader-count {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--color-brass);
		letter-spacing: 0.1em;
	}

	.preloader-skip {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-ivory-faint);
		background: none;
		border: none;
		padding: 0.4rem 0.6rem;
	}
</style>
