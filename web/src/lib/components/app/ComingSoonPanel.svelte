<script lang="ts">
	import GlassPanel from './GlassPanel.svelte';

	let {
		eyebrow,
		title,
		phase,
		description
	}: {
		eyebrow: string;
		title: string;
		phase: string;
		description: string;
	} = $props();
</script>

<header class="page-head">
	<p class="label label-signal">{eyebrow}</p>
	<h1>{title}</h1>
</header>

<GlassPanel>
	<p class="phase-tag">{phase}</p>
	<p class="description">{description}</p>
</GlassPanel>

<style>
	.page-head {
		margin-bottom: 2rem;
	}

	.page-head h1 {
		font-size: clamp(1.6rem, 2.8vw, 2.1rem);
		margin-top: 0.4rem;
	}

	.phase-tag {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.72rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-signal);
		background: color-mix(in srgb, var(--color-signal) 12%, transparent);
		border: 1px solid color-mix(in srgb, var(--color-signal) 30%, transparent);
		border-radius: 6px;
		padding: 0.3rem 0.6rem;
		margin-bottom: 1rem;
	}

	.description {
		color: var(--color-ivory-dim);
		font-size: 0.95rem;
		line-height: 1.6;
		max-width: 36rem;
	}
</style>
