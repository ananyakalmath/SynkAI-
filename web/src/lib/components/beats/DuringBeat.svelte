<script lang="ts">
	import { lifecycle, duringTranscript, askSynk } from '#lib/content.js';

	const step = lifecycle[1];

	const tagLabel: Record<string, string> = {
		decision: 'decision',
		risk: 'risk',
		question: 'question'
	};

	const waveformBars = Array.from({ length: 14 }, (_, i) => i);
</script>

<div class="beat-inner">
	<p class="label label-signal">{step.step} — {step.label}</p>
	<h3>{step.title}</h3>
	<p class="beat-body">{step.body}</p>

	<div class="card transcript-card">
		<div class="transcript-head">
			<p class="card-title">Live transcript</p>
			<div class="waveform" aria-hidden="true">
				{#each waveformBars as i (i)}
					<span style={`--d:${(i % 5) * 70}ms; --h:${30 + ((i * 13) % 55)}%`}></span>
				{/each}
			</div>
		</div>
		<ol class="transcript-lines">
			{#each duringTranscript as line (line.t)}
				<li>
					<span class="transcript-time">{line.t}</span>
					<span class="transcript-speaker">{line.speaker}</span>
					<span class="transcript-text">{line.text}</span>
					{#if line.tag}
						<span class="tag tag-{line.tag}">{tagLabel[line.tag]}</span>
					{/if}
				</li>
			{/each}
		</ol>
	</div>

	<div class="card ask-card">
		<p class="card-title">Ask Synk</p>
		<p class="ask-question">{askSynk.question}</p>
		<p class="ask-answer">{askSynk.answer}</p>
	</div>
	<p class="illustrative-note">illustrative preview — not a live capture</p>
</div>

<style>
	.beat-inner {
		max-width: 46rem;
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
	}

	.transcript-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.6rem;
	}

	.waveform {
		display: flex;
		align-items: center;
		gap: 2px;
		height: 18px;
	}

	.waveform span {
		width: 2px;
		height: var(--h);
		background: var(--color-signal-dim);
		animation: wave 1.1s ease-in-out infinite;
		animation-delay: var(--d);
	}

	@keyframes wave {
		0%,
		100% {
			transform: scaleY(0.4);
			opacity: 0.6;
		}
		50% {
			transform: scaleY(1);
			opacity: 1;
		}
	}

	.transcript-lines {
		margin: 0;
		padding: 0;
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		font-family: var(--font-mono);
		font-size: 0.8rem;
	}

	.transcript-lines li {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.5rem;
	}

	.transcript-time {
		color: var(--color-ivory-faint);
	}

	.transcript-speaker {
		color: var(--color-brass);
	}

	.transcript-text {
		color: var(--color-ivory);
		flex: 1 1 14rem;
		font-family: var(--font-sans);
		font-size: 0.875rem;
	}

	.tag {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		border: 1px solid currentColor;
	}

	.tag-decision {
		color: var(--color-signal);
	}

	.tag-risk {
		color: var(--color-risk);
	}

	.tag-question {
		color: var(--color-ivory-dim);
	}

	.ask-question {
		font-size: 0.9rem;
		color: var(--color-ivory);
		margin-top: 0.5rem;
	}

	.ask-answer {
		font-size: 0.9rem;
		color: var(--color-ivory-dim);
		margin-top: 0.4rem;
		border-left: 2px solid var(--color-signal-dim);
		padding-left: 0.7rem;
	}
</style>
