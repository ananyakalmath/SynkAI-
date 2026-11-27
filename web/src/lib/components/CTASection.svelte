<script lang="ts">
	import { enhance } from '$app/forms';
	import { cta } from '#lib/content.js';
	import type { SubmitFunction } from '$app/forms';

	let {
		form
	}: { form: { success?: boolean; error?: string; email?: string; company?: string } | null } =
		$props();

	let submitting = $state(false);

	const onSubmit: SubmitFunction = () => {
		submitting = true;
		return async ({ update }) => {
			await update();
			submitting = false;
		};
	};
</script>

<section class="cta" id="early-access" aria-labelledby="cta-heading">
	<div class="cta-inner">
		<p class="label label-signal">request early access</p>
		<h2 id="cta-heading">{cta.heading}</h2>
		<p class="cta-body">{cta.body}</p>

		{#if form?.success}
			<p class="cta-success" role="status">{cta.successMessage}</p>
		{:else}
			<form method="POST" use:enhance={onSubmit} class="cta-form" novalidate>
				<div class="field">
					<label for="email">Work email</label>
					<input
						id="email"
						name="email"
						type="email"
						required
						autocomplete="email"
						value={form?.email ?? ''}
					/>
				</div>
				<div class="field">
					<label for="company">Company <span class="optional">(optional)</span></label>
					<input
						id="company"
						name="company"
						type="text"
						autocomplete="organization"
						value={form?.company ?? ''}
					/>
				</div>

				<!-- honeypot: invisible to people, visible to bots that fill every field -->
				<div class="honeypot" aria-hidden="true">
					<label for="website">Website</label>
					<input id="website" name="website" type="text" tabindex="-1" autocomplete="off" />
				</div>

				{#if form?.error}
					<p class="cta-error" role="alert">{form.error}</p>
				{/if}

				<button type="submit" class="cta-submit" disabled={submitting}>
					{submitting ? 'sending…' : cta.submitLabel}
				</button>
			</form>
		{/if}
	</div>
</section>

<style>
	.cta {
		padding: clamp(5rem, 14vw, 10rem) clamp(1.25rem, 5vw, 4rem);
		background: var(--color-obsidian);
	}

	.cta-inner {
		max-width: 32rem;
		margin: 0 auto;
		text-align: center;
	}

	h2 {
		font-size: clamp(2.25rem, 5vw, 3.5rem);
		margin-top: 0.5rem;
	}

	.cta-body {
		margin-top: 1rem;
		color: var(--color-ivory-dim);
	}

	.cta-form {
		margin-top: 2.25rem;
		display: flex;
		flex-direction: column;
		gap: 1.1rem;
		text-align: left;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.field label {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--color-ivory-dim);
	}

	.optional {
		text-transform: none;
		color: var(--color-ivory-faint);
	}

	.field input {
		background: var(--color-obsidian-2);
		border: 1px solid var(--color-graphite-2);
		border-radius: 8px;
		padding: 0.7rem 0.85rem;
		color: var(--color-ivory);
		font-size: 1rem;
	}

	.field input:focus-visible {
		border-color: var(--color-signal);
	}

	.honeypot {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		opacity: 0;
		pointer-events: none;
	}

	.cta-submit {
		margin-top: 0.4rem;
		background: var(--color-brass);
		color: var(--color-obsidian);
		font-weight: 600;
		border: none;
		border-radius: 8px;
		padding: 0.85rem 1.4rem;
		font-size: 0.95rem;
		transition: background-color 0.2s ease;
	}

	.cta-submit:hover:not(:disabled) {
		background: var(--color-brass-bright);
	}

	.cta-submit:disabled {
		opacity: 0.6;
		cursor: default;
	}

	.cta-error {
		color: var(--color-risk);
		font-size: 0.9rem;
	}

	.cta-success {
		margin-top: 2rem;
		color: var(--color-good);
		font-size: 1.05rem;
	}
</style>
