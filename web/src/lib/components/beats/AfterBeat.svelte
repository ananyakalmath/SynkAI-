<script lang="ts">
	import { lifecycle, minutes } from '#lib/content.js';

	const step = lifecycle[2];
</script>

<div class="beat-inner">
	<p class="label label-signal">{step.step} — {step.label}</p>
	<h3>{step.title}</h3>
	<p class="beat-body">{step.body}</p>

	<div class="cards">
		<div class="card">
			<p class="card-title">Decisions</p>
			<ul>
				{#each minutes.decisions as item (item)}
					<li>{item}</li>
				{/each}
			</ul>
			<p class="card-title" style="margin-top:0.7rem">Open questions</p>
			<ul>
				{#each minutes.openQuestions as item (item)}
					<li>{item}</li>
				{/each}
			</ul>
		</div>
		<div class="card">
			<p class="card-title">Action items</p>
			<ul class="action-list">
				{#each minutes.actionItems as item (item.task)}
					<li>
						<span class="action-owner">{item.owner}</span>
						<span class="action-task">{item.task}</span>
						<span class="action-due">due {item.due}</span>
					</li>
				{/each}
			</ul>
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

	.action-list {
		list-style: none;
		padding-left: 0;
	}

	.action-list li {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid var(--color-graphite-2);
	}

	.action-list li:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}

	.action-owner {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--color-brass);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.action-task {
		color: var(--color-ivory);
		font-size: 0.9rem;
	}

	.action-due {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--color-ivory-faint);
	}

	@media (max-width: 640px) {
		.cards {
			grid-template-columns: 1fr;
		}
	}
</style>
