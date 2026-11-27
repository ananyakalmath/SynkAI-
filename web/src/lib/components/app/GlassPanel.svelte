<script lang="ts">
	// The frosted-glass panel used throughout the app shell — login, dashboard cards,
	// the calendar's detail panel, etc. Quiet luxury: a hairline border, a soft
	// obsidian fill with light blur, never a heavy drop shadow (DESIGN.md §3).
	import type { Snippet } from 'svelte';

	let {
		tight = false,
		glow = 'none',
		children
	}: {
		tight?: boolean;
		glow?: 'none' | 'brass' | 'signal';
		children: Snippet;
	} = $props();
</script>

<div
	class="glass-panel"
	class:tight
	class:glow-brass={glow === 'brass'}
	class:glow-signal={glow === 'signal'}
>
	{@render children()}
</div>

<style>
	.glass-panel {
		background: color-mix(in srgb, var(--color-obsidian-2) 78%, transparent);
		border: 1px solid var(--color-graphite-2);
		border-radius: 16px;
		padding: clamp(1.25rem, 2.5vw, 2rem);
		backdrop-filter: blur(18px);
		-webkit-backdrop-filter: blur(18px);
	}

	.glass-panel.tight {
		padding: 1rem 1.25rem;
	}

	.glass-panel.glow-brass {
		box-shadow: 0 0 60px -20px color-mix(in srgb, var(--color-brass) 35%, transparent);
	}

	.glass-panel.glow-signal {
		box-shadow: 0 0 60px -20px color-mix(in srgb, var(--color-signal) 35%, transparent);
	}
</style>
