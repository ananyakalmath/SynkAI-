<script lang="ts">
	// Login/sign-up backdrop: "arriving at the boardroom" — a blurred, slowly-breathing
	// still of the room behind the frosted glass panel. This intentionally uses the
	// static-still tier from DESIGN.md's room journey rather than the marketing page's
	// pinned Three.js scene: a lightweight backdrop a user sees on every sign-in, not a
	// one-time cinematic entrance. The breathing motion is pure CSS and turns off under
	// prefers-reduced-motion (handled globally in layout.css).
	import StaticBoardroomStill from '#lib/components/StaticBoardroomStill.svelte';
</script>

<div class="backdrop" aria-hidden="true">
	<div class="still-wrap">
		<StaticBoardroomStill caption="" />
	</div>
	<div class="vignette"></div>
</div>

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		z-index: 0;
		overflow: hidden;
		background: var(--color-obsidian);
	}

	.still-wrap {
		position: absolute;
		inset: -5%;
		filter: blur(22px) saturate(1.1) brightness(0.75);
		animation: breathe 14s ease-in-out infinite;
	}

	.still-wrap :global(.still-svg) {
		border: none;
		border-radius: 0;
	}

	.still-wrap :global(figcaption) {
		display: none;
	}

	.vignette {
		position: absolute;
		inset: 0;
		background: radial-gradient(
			ellipse at center,
			transparent 35%,
			color-mix(in srgb, var(--color-obsidian) 75%, transparent) 100%
		);
	}

	@keyframes breathe {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.04);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.still-wrap {
			animation: none;
		}
	}
</style>
