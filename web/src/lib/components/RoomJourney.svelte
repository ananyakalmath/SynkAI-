<script lang="ts">
	import { onMount } from 'svelte';
	import { walkIn, nextMeeting } from '#lib/content.js';
	import { getReducedMotion } from '#lib/motion/reducedMotion.svelte.js';
	import { loadGsap } from '#lib/motion/registerGsap.js';
	import { clamp01, smoothstep } from '#lib/motion/easing.js';
	import StaticBoardroomStill from './StaticBoardroomStill.svelte';
	import BeforeBeat from './beats/BeforeBeat.svelte';
	import DuringBeat from './beats/DuringBeat.svelte';
	import AfterBeat from './beats/AfterBeat.svelte';
	import FollowThroughBeat from './beats/FollowThroughBeat.svelte';

	const RANGES = {
		walkin: [0.0, 0.14] as const,
		tableAlive: [0.17, 0.3] as const,
		before: [0.26, 0.395] as const,
		during: [0.395, 0.53] as const,
		after: [0.53, 0.665] as const,
		followthrough: [0.665, 0.8] as const,
		nextMeeting: [0.84, 1.0] as const
	};

	function beatOpacity(p: number, [start, end]: readonly [number, number], feather = 0.035) {
		const fadeIn = smoothstep(start, start + feather, p);
		const fadeOut = 1 - smoothstep(end - feather, end, p);
		return Math.max(0, Math.min(fadeIn, fadeOut));
	}

	let journeyEl: HTMLElement = $state()!;
	let stageEl: HTMLDivElement = $state()!;
	let canvasEl: HTMLCanvasElement = $state()!;

	let cinematic = $state(false);
	let progress = $state(0);

	const op = $derived({
		walkin: beatOpacity(progress, RANGES.walkin),
		tableAlive: beatOpacity(progress, RANGES.tableAlive),
		before: beatOpacity(progress, RANGES.before),
		during: beatOpacity(progress, RANGES.during),
		after: beatOpacity(progress, RANGES.after),
		followthrough: beatOpacity(progress, RANGES.followthrough),
		nextMeeting: beatOpacity(progress, RANGES.nextMeeting)
	});

	const followThroughLocalProgress = $derived(
		clamp01(
			(progress - RANGES.followthrough[0]) / (RANGES.followthrough[1] - RANGES.followthrough[0])
		)
	);

	onMount(() => {
		if (getReducedMotion()) return;
		cinematic = true;

		let disposed = false;
		let teardown: (() => void) | undefined;

		void (async () => {
			const mobile = window.innerWidth < 768;
			const [{ createBoardroomScene }, { ScrollTrigger }] = await Promise.all([
				import('#lib/three/boardroom.js'),
				loadGsap()
			]);
			if (disposed) return;

			const handle = createBoardroomScene(canvasEl, mobile);

			const resize = () => {
				const rect = stageEl.getBoundingClientRect();
				handle.resize(rect.width, rect.height);
			};
			resize();
			window.addEventListener('resize', resize);

			let tabVisible = document.visibilityState === 'visible';
			let inView = false;
			const syncRunning = () => handle.setRunning(tabVisible && inView);

			const onVisibility = () => {
				tabVisible = document.visibilityState === 'visible';
				syncRunning();
			};
			document.addEventListener('visibilitychange', onVisibility);

			const observer = new IntersectionObserver(
				([entry]) => {
					inView = entry.isIntersecting;
					syncRunning();
				},
				{ threshold: 0.01 }
			);
			observer.observe(journeyEl);

			const trackVh = mobile ? 420 : 640;
			journeyEl.style.height = `${trackVh}vh`;

			const trigger = ScrollTrigger.create({
				trigger: journeyEl,
				start: 'top top',
				end: 'bottom bottom',
				pin: stageEl,
				scrub: true,
				onUpdate(self) {
					progress = self.progress;
					handle.setProgress(self.progress);
				}
			});

			teardown = () => {
				window.removeEventListener('resize', resize);
				document.removeEventListener('visibilitychange', onVisibility);
				observer.disconnect();
				trigger.kill();
				handle.dispose();
			};
		})();

		return () => {
			disposed = true;
			teardown?.();
		};
	});
</script>

<section
	class="journey"
	class:cinematic
	bind:this={journeyEl}
	aria-label="The SynkAI meeting lifecycle"
>
	{#if cinematic}
		<div class="stage" bind:this={stageEl}>
			<canvas bind:this={canvasEl} class="journey-canvas" aria-hidden="true"></canvas>

			<div class="beats">
				<div class="beat beat-center" style:opacity={op.walkin} aria-hidden={op.walkin < 0.05}>
					<p class="label label-signal">the walk-in</p>
					<h2>{walkIn.headline}</h2>
				</div>

				<div
					class="beat beat-center"
					style:opacity={op.tableAlive}
					aria-hidden={op.tableAlive < 0.05}
				>
					<p class="label label-signal">the table comes alive</p>
					<h2>One continuous intelligence loop.</h2>
				</div>

				<div class="beat beat-panel" style:opacity={op.before} aria-hidden={op.before < 0.05}>
					<BeforeBeat />
				</div>

				<div class="beat beat-panel" style:opacity={op.during} aria-hidden={op.during < 0.05}>
					<DuringBeat />
				</div>

				<div class="beat beat-panel" style:opacity={op.after} aria-hidden={op.after < 0.05}>
					<AfterBeat />
				</div>

				<div
					class="beat beat-panel"
					style:opacity={op.followthrough}
					aria-hidden={op.followthrough < 0.05}
				>
					<FollowThroughBeat progress={followThroughLocalProgress} />
				</div>

				<div
					class="beat beat-center"
					style:opacity={op.nextMeeting}
					aria-hidden={op.nextMeeting < 0.05}
				>
					<p class="label label-signal">next meeting</p>
					<h2>{nextMeeting.line}</h2>
				</div>
			</div>
		</div>
	{:else}
		<div class="static-journey">
			<StaticBoardroomStill />

			<div class="static-beat">
				<p class="label label-signal">the ai boardroom copilot</p>
				<h2>{walkIn.headline}</h2>
			</div>

			<div class="static-beat">
				<BeforeBeat />
			</div>
			<div class="static-beat">
				<DuringBeat />
			</div>
			<div class="static-beat">
				<AfterBeat />
			</div>
			<div class="static-beat">
				<FollowThroughBeat />
			</div>

			<div class="static-beat">
				<p class="label label-signal">next meeting</p>
				<h2>{nextMeeting.line}</h2>
			</div>
		</div>
	{/if}
</section>

<style>
	.journey {
		position: relative;
		background: var(--color-obsidian);
	}

	.stage {
		position: relative;
		height: 100vh;
		overflow: hidden;
	}

	.journey-canvas {
		position: absolute;
		inset: 0;
		display: block;
		width: 100%;
		height: 100%;
	}

	.beats {
		position: absolute;
		inset: 0;
	}

	.beat {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 clamp(1.25rem, 5vw, 4rem);
		will-change: opacity;
	}

	.beat-center {
		flex-direction: column;
		gap: 1rem;
		text-align: center;
	}

	.beat-center h2 {
		font-size: clamp(2.25rem, 5.5vw, 4.5rem);
		max-width: 50rem;
	}

	.beat-panel {
		justify-content: flex-start;
		align-items: flex-end;
		padding-bottom: clamp(2rem, 6vw, 5rem);
	}

	.static-journey {
		max-width: 1200px;
		margin: 0 auto;
		padding: clamp(5rem, 12vw, 9rem) clamp(1.25rem, 5vw, 4rem);
		display: flex;
		flex-direction: column;
		gap: clamp(3rem, 8vw, 5rem);
	}

	.static-beat {
		display: flex;
		justify-content: center;
	}

	.static-beat h2 {
		font-size: clamp(2rem, 5vw, 3.5rem);
		text-align: center;
		max-width: 40rem;
	}

	.static-beat:first-of-type,
	.static-beat:last-of-type {
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		text-align: center;
	}

	@media (prefers-reduced-motion: no-preference) {
		.static-beat {
			animation: beat-fade-in 0.4s ease both;
			animation-timeline: view();
			animation-range: entry 0% cover 25%;
		}
	}

	@keyframes beat-fade-in {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
