<script lang="ts">
	import { onMount } from 'svelte';
	import { doors, product } from '#lib/content.js';
	import { getReducedMotion } from '#lib/motion/reducedMotion.svelte.js';
	import { loadGsap } from '#lib/motion/registerGsap.js';

	let sectionEl: HTMLElement = $state()!;
	let stageEl: HTMLDivElement = $state()!;
	let leftDoor: HTMLDivElement = $state()!;
	let rightDoor: HTMLDivElement = $state()!;

	let cinematic = $state(false);

	onMount(() => {
		if (getReducedMotion()) return;
		cinematic = true;

		let cleanup: (() => void) | undefined;

		void loadGsap().then(({ gsap, ScrollTrigger }) => {
			const trigger = ScrollTrigger.create({
				trigger: sectionEl,
				start: 'top top',
				end: '+=140%',
				pin: stageEl,
				scrub: true,
				onUpdate(self) {
					const p = self.progress;
					gsap.set(leftDoor, { xPercent: -p * 72 });
					gsap.set(rightDoor, { xPercent: p * 72 });
				}
			});
			cleanup = () => trigger.kill();
		});

		return () => cleanup?.();
	});
</script>

<section class="doors-section" class:cinematic bind:this={sectionEl} aria-label="Entering SynkAI">
	<div class="doors-stage" bind:this={stageEl}>
		<div class="room-glimpse" aria-hidden="true"></div>

		<div class="door door-left" bind:this={leftDoor} aria-hidden="true">
			<span class="door-grain"></span>
		</div>
		<div class="door door-right" bind:this={rightDoor} aria-hidden="true">
			<span class="door-grain"></span>
		</div>

		<div class="doors-etch" aria-hidden="true">{product.name}</div>

		<div class="doors-content">
			<p class="label label-signal">{product.name.toLowerCase()}</p>
			<h1>{doors.headline}</h1>
			<p class="doors-sub">{product.tagline.toLowerCase()} — in development</p>
		</div>
	</div>
</section>

<style>
	.doors-section {
		position: relative;
		background: var(--color-obsidian);
	}

	.doors-stage {
		position: relative;
		height: 100vh;
		overflow: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.room-glimpse {
		position: absolute;
		inset: 0;
		background:
			radial-gradient(ellipse at 50% 60%, rgba(201, 164, 103, 0.22), transparent 55%),
			radial-gradient(ellipse at 50% 100%, rgba(95, 225, 224, 0.08), transparent 60%),
			var(--color-obsidian);
	}

	.door {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 50%;
		background:
			linear-gradient(135deg, rgba(243, 239, 230, 0.07), rgba(243, 239, 230, 0.02)),
			var(--color-graphite);
		backdrop-filter: blur(2px);
		border: 1px solid var(--color-graphite-2);
	}

	.door-left {
		left: 0;
		border-right: 1px solid rgba(201, 164, 103, 0.4);
	}

	.door-right {
		right: 0;
		border-left: 1px solid rgba(201, 164, 103, 0.4);
	}

	.door-grain {
		position: absolute;
		inset: 0;
		opacity: 0.5;
		background-image: repeating-linear-gradient(
			90deg,
			rgba(255, 255, 255, 0.015) 0px,
			rgba(255, 255, 255, 0.015) 1px,
			transparent 1px,
			transparent 7px
		);
	}

	.doors-etch {
		position: absolute;
		font-family: var(--font-display);
		font-size: clamp(2rem, 6vw, 4.5rem);
		letter-spacing: 0.06em;
		color: rgba(243, 239, 230, 0.14);
		z-index: 1;
		pointer-events: none;
	}

	.doors-content {
		position: relative;
		z-index: 2;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.1rem;
		padding: 0 1.5rem;
		max-width: 46rem;
	}

	.doors-content h1 {
		font-size: clamp(2.75rem, 7vw, 6.5rem);
		line-height: 0.98;
	}

	.doors-sub {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		letter-spacing: 0.08em;
		color: var(--color-ivory-dim);
	}

	/* static / reduced-motion / no-JS: doors sit open, headline simply fades in */
	.doors-section:not(.cinematic) .door {
		display: none;
	}

	.doors-section:not(.cinematic) .doors-etch {
		display: none;
	}

	.doors-section.cinematic .doors-stage {
		will-change: contents;
	}

	@media (prefers-reduced-motion: no-preference) {
		.doors-section:not(.cinematic) .doors-content {
			animation: doors-fade-in 0.4s ease both;
		}
	}

	@keyframes doors-fade-in {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
