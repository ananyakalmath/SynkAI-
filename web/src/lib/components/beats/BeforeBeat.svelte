<script lang="ts">
	import { lifecycle, beforeDemo } from '#lib/content.js';

	const step = lifecycle[0];
</script>

<div class="beat-inner">
	<p class="label label-signal">{step.step} — {step.label}</p>
	<h3>{step.title}</h3>
	<p class="beat-body">{step.body}</p>

	<div class="cards">
		<div class="card">
			<p class="card-title">Agenda</p>
			<ul>
				{#each beforeDemo.agenda as item (item)}
					<li>{item}</li>
				{/each}
			</ul>
		</div>
		<div class="card">
			<p class="card-title">Pre-meeting brief</p>
			<p class="card-text">{beforeDemo.brief}</p>
		</div>
	</div>
	<p class="illustrative-note">illustrative preview — not a live capture</p>
</div>

<style>
	.beat-inner {
		max-width: 44rem;
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
	}

	h3 {
		font-size: clamp(1.5rem, 2.6vw, 2.25rem);
	}

	.beat-body {
		color: var(--color-ivory-dim);
		max-width: 38rem;
	}

	.cards {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.75rem;
		margin-top: 0.4rem;
	}

	.card {
		background: rgba(12, 14, 18, 0.72);
		border: 1px solid var(--color-graphite-2);
		border-radius: 10px;
		padding: 1rem 1.1rem;
		backdrop-filter: blur(6px);
	}

	.card-title {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-signal);
		margin-bottom: 0.5rem;
	}

	.card ul {
		margin: 0;
		padding-left: 1.1rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		font-size: 0.9rem;
		color: var(--color-ivory-dim);
	}

	.card-text {
		font-size: 0.9rem;
		color: var(--color-ivory-dim);
	}

	@media (max-width: 640px) {
		.cards {
			grid-template-columns: 1fr;
		}
	}
</style>
