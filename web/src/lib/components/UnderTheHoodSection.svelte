<script lang="ts">
	import { underTheHood, agentPipeline } from '#lib/content.js';

	const parser = agentPipeline[0];
	const coordinator = agentPipeline[agentPipeline.length - 1];
	const middle = agentPipeline.slice(1, -1);
</script>

<section class="hood" id="under-the-hood" aria-labelledby="hood-heading">
	<div class="hood-inner">
		<p class="label label-signal">under the hood</p>
		<h2 id="hood-heading">Built to run close to your own data.</h2>
		<p class="hood-intro">{underTheHood.intro}</p>

		<div class="points">
			{#each underTheHood.points as point (point.title)}
				<div class="point">
					<h3>{point.title}</h3>
					<p>{point.body}</p>
				</div>
			{/each}
		</div>

		<div
			class="diagram"
			role="img"
			aria-label="Pipeline diagram: parser agent feeds the summary, action-item, decision, deadline and risk agents, all reconciled by a coordinator agent."
		>
			<div class="diagram-node diagram-node-solo">
				<p class="node-label">{parser.name}</p>
				<p class="node-role">{parser.role}</p>
			</div>

			<div class="diagram-connector" aria-hidden="true">
				<span class="pulse"></span>
			</div>

			<div class="diagram-column">
				{#each middle as agent (agent.id)}
					<div class="diagram-node">
						<p class="node-label">{agent.name}</p>
						<p class="node-role">{agent.role}</p>
					</div>
				{/each}
			</div>

			<div class="diagram-connector" aria-hidden="true">
				<span class="pulse" style="animation-delay: 0.6s"></span>
			</div>

			<div class="diagram-node diagram-node-solo">
				<p class="node-label">{coordinator.name}</p>
				<p class="node-role">{coordinator.role}</p>
			</div>
		</div>
		<p class="illustrative-note">simplified diagram of the LangGraph multi-agent workflow</p>
	</div>
</section>

<style>
	.hood {
		padding: clamp(5rem, 12vw, 9rem) clamp(1.25rem, 5vw, 4rem);
		background: var(--color-obsidian-2);
		border-top: 1px solid var(--color-graphite-2);
		border-bottom: 1px solid var(--color-graphite-2);
	}

	.hood-inner {
		max-width: 1200px;
		margin: 0 auto;
	}

	h2 {
		font-size: clamp(2rem, 4.5vw, 3.25rem);
		margin-top: 0.5rem;
		max-width: 34rem;
	}

	.hood-intro {
		margin-top: 1.25rem;
		max-width: 40rem;
		color: var(--color-ivory-dim);
		font-size: 1.0625rem;
	}

	.points {
		margin-top: clamp(2.5rem, 6vw, 4rem);
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 1.5rem;
	}

	.point h3 {
		font-size: 1.15rem;
		font-weight: 600;
		font-family: var(--font-sans);
		letter-spacing: -0.01em;
	}

	.point p {
		margin-top: 0.6rem;
		color: var(--color-ivory-dim);
		font-size: 0.95rem;
	}

	.diagram {
		margin-top: clamp(3rem, 7vw, 5rem);
		display: flex;
		align-items: center;
		gap: 0;
		overflow-x: auto;
		padding-bottom: 0.5rem;
	}

	.diagram-column {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.diagram-node {
		border: 1px solid var(--color-graphite-2);
		background: var(--color-graphite);
		border-radius: 8px;
		padding: 0.65rem 0.9rem;
		min-width: 11rem;
	}

	.diagram-node-solo {
		border-color: var(--color-signal-dim);
		box-shadow: 0 0 24px rgba(95, 225, 224, 0.12);
	}

	.node-label {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--color-signal);
		letter-spacing: 0.03em;
	}

	.node-role {
		font-size: 0.8rem;
		color: var(--color-ivory-dim);
		margin-top: 0.2rem;
	}

	.diagram-connector {
		position: relative;
		width: clamp(2rem, 5vw, 4rem);
		height: 1px;
		background: var(--color-graphite-2);
		flex-shrink: 0;
	}

	.pulse {
		position: absolute;
		top: -2px;
		left: 0;
		width: 5px;
		height: 5px;
		border-radius: 999px;
		background: var(--color-signal);
		box-shadow: 0 0 8px var(--color-signal);
		animation: travel 2.4s ease-in-out infinite;
	}

	@keyframes travel {
		0% {
			left: 0;
			opacity: 0;
		}
		10% {
			opacity: 1;
		}
		90% {
			opacity: 1;
		}
		100% {
			left: calc(100% - 5px);
			opacity: 0;
		}
	}

	@media (max-width: 860px) {
		.points {
			grid-template-columns: 1fr;
		}
	}
</style>
