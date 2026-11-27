<script lang="ts">
	import { fly, fade } from 'svelte/transition';
	import { lifecycle, tasks as baseTasks } from '#lib/content.js';

	let { progress = null }: { progress?: number | null } = $props();

	const step = lifecycle[3];

	type Status = 'on-track' | 'overdue' | 'done';

	const columns: { id: Status; label: string }[] = [
		{ id: 'on-track', label: 'On track' },
		{ id: 'overdue', label: 'Overdue' },
		{ id: 'done', label: 'Done' }
	];

	// the "P. Nair" task demonstrates the overdue → done flip when the journey
	// is scroll-driven (progress supplied). without a scroll driver, every
	// task simply shows its resting state.
	const liveTasks = $derived(
		baseTasks.map((task) => {
			if (task.owner !== 'P. Nair' || progress === null) return task;
			const status: Status = progress < 0.55 ? 'overdue' : 'done';
			return { ...task, status };
		})
	);
</script>

<div class="beat-inner">
	<p class="label label-signal">{step.step} — {step.label}</p>
	<h3>{step.title}</h3>
	<p class="beat-body">{step.body}</p>

	<div class="board">
		{#each columns as column (column.id)}
			<div class="column">
				<p class="column-title">
					{column.label}
					{#if column.id === 'overdue'}
						<span class="chime" aria-hidden="true">&#128276;</span>
					{/if}
				</p>
				<div class="column-cards">
					{#each liveTasks.filter((t) => t.status === column.id) as task (task.task)}
						<div
							class="task-card status-{task.status}"
							in:fly={{ y: 10, duration: 350 }}
							out:fade={{ duration: 200 }}
						>
							<span class="task-owner">{task.owner}</span>
							<span class="task-text">{task.task}</span>
							<span class="task-due">due {task.due}</span>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>
	<p class="illustrative-note">illustrative preview — not a live capture</p>
</div>

<style>
	.beat-inner {
		max-width: 52rem;
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

	.board {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.7rem;
	}

	.column {
		background: rgba(12, 14, 18, 0.6);
		border: 1px solid var(--color-graphite-2);
		border-radius: 10px;
		padding: 0.8rem;
		min-height: 9rem;
	}

	.column-title {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--color-ivory-faint);
		margin-bottom: 0.6rem;
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.chime {
		font-size: 0.75rem;
	}

	.column-cards {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.task-card {
		border: 1px solid var(--color-graphite-2);
		border-left: 3px solid var(--color-ivory-faint);
		background: var(--color-obsidian-2);
		border-radius: 6px;
		padding: 0.55rem 0.65rem;
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}

	.task-card.status-overdue {
		border-left-color: var(--color-risk);
	}

	.task-card.status-done {
		border-left-color: var(--color-good);
	}

	.task-owner {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--color-brass);
	}

	.task-text {
		font-size: 0.85rem;
		color: var(--color-ivory);
	}

	.task-due {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--color-ivory-faint);
	}

	@media (max-width: 760px) {
		.board {
			grid-template-columns: 1fr;
		}
	}
</style>
