<script lang="ts">
	import { enhance } from '$app/forms';
	import BoardroomBackdrop from '#lib/components/app/BoardroomBackdrop.svelte';
	import GlassPanel from '#lib/components/app/GlassPanel.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	const pending = $derived(form?.pending ?? data.pending);
	let submitting = $state(false);
</script>

<svelte:head>
	<title>Set up your account — SynkAI</title>
</svelte:head>

<div class="stage">
	<BoardroomBackdrop />
	<div class="panel-wrap">
		{#if pending}
			<GlassPanel glow="signal">
				<p class="label label-signal">Workspace</p>
				<h1>Waiting for approval</h1>
				<p class="body-copy">
					Your request to join <strong>
						{data.user.workspace?.company_name ?? 'this workspace'}
					</strong>
					is pending. An admin there needs to approve it before you can use SynkAI.
				</p>
				<div class="button-row">
					<form method="POST" action="?/checkAgain" use:enhance>
						<button type="submit" class="primary-button">Check again</button>
					</form>
					<form method="POST" action="/logout">
						<button type="submit" class="ghost-button">Sign out</button>
					</form>
				</div>
			</GlassPanel>
		{:else}
			<GlassPanel glow="brass">
				<p class="label label-signal">SynkAI</p>
				<h1>Set up your account</h1>
				<p class="body-copy">Just a few details before your boardroom is ready.</p>

				<form
					method="POST"
					action="?/submit"
					use:enhance={() => {
						submitting = true;
						return async ({ update }) => {
							await update();
							submitting = false;
						};
					}}
				>
					<input type="hidden" name="invite_code" value={data.inviteCode ?? ''} />

					<label class="field-label" for="full-name">Full name</label>
					<input
						id="full-name"
						name="full_name"
						required
						class="text-field"
						value={data.user.full_name ?? ''}
					/>

					<label class="field-label" for="work-email">Work email</label>
					<input id="work-email" class="text-field" value={data.user.email} disabled />

					<label class="field-label" for="role-title">Role / title</label>
					<input
						id="role-title"
						name="role_title"
						required
						class="text-field"
						placeholder="e.g. CEO, Manager, Engineer"
					/>

					{#if data.inviteCode}
						<p class="invite-note">
							You have an invite — continuing will join that workspace directly.
						</p>
					{:else}
						<label class="field-label" for="company-name">Company name</label>
						<input
							id="company-name"
							name="company_name"
							class="text-field"
							placeholder="Acme Inc."
						/>
						<p class="hint">
							If someone at your company already set up a SynkAI workspace, you'll be asked to wait
							for their approval to join it — matched by your email domain, not the company name you
							type here. Personal email providers (Gmail, Outlook, etc.) always get a brand new
							workspace; ask an admin to invite you to join an existing one instead.
						</p>
					{/if}

					{#if form?.error}
						<p class="error" role="alert">{form.error}</p>
					{/if}

					<button type="submit" class="primary-button" disabled={submitting}>
						{submitting ? 'Setting up…' : 'Continue'}
					</button>
				</form>
			</GlassPanel>
		{/if}
	</div>
</div>

<style>
	.stage {
		position: relative;
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem 1.25rem;
	}

	.panel-wrap {
		position: relative;
		z-index: 1;
		width: 100%;
		max-width: 28rem;
	}

	h1 {
		font-size: clamp(1.5rem, 2.6vw, 2rem);
		margin: 0.4rem 0 0.6rem;
	}

	.body-copy {
		color: var(--color-ivory-dim);
		font-size: 0.95rem;
		margin-bottom: 1.5rem;
		line-height: 1.6;
	}

	.field-label {
		display: block;
		font-size: 0.78rem;
		letter-spacing: 0.04em;
		color: var(--color-ivory-dim);
		margin-bottom: 0.4rem;
	}

	.text-field {
		width: 100%;
		background: var(--color-obsidian);
		border: 1px solid var(--color-graphite-2);
		border-radius: 8px;
		padding: 0.7rem 0.85rem;
		color: var(--color-ivory);
		font-size: 0.95rem;
		margin-bottom: 1rem;
	}

	.text-field:disabled {
		opacity: 0.55;
	}

	.text-field:focus {
		border-color: var(--color-brass);
		outline: none;
	}

	.invite-note {
		font-size: 0.85rem;
		color: var(--color-signal);
		background: color-mix(in srgb, var(--color-signal) 12%, transparent);
		border: 1px solid color-mix(in srgb, var(--color-signal) 30%, transparent);
		border-radius: 8px;
		padding: 0.6rem 0.8rem;
		margin-bottom: 1.25rem;
	}

	.hint {
		font-size: 0.8rem;
		color: var(--color-ivory-faint);
		line-height: 1.5;
		margin-bottom: 1.25rem;
	}

	.primary-button {
		width: 100%;
		padding: 0.75rem 1rem;
		border-radius: 10px;
		border: none;
		background: var(--color-brass);
		color: var(--color-obsidian);
		font-weight: 600;
		font-size: 0.92rem;
	}

	.primary-button:hover:not(:disabled) {
		background: var(--color-brass-bright);
	}

	.primary-button:disabled {
		opacity: 0.6;
	}

	.ghost-button {
		width: 100%;
		padding: 0.75rem 1rem;
		border-radius: 10px;
		border: 1px solid var(--color-graphite-2);
		background: transparent;
		color: var(--color-ivory-dim);
		font-size: 0.88rem;
	}

	.ghost-button:hover {
		border-color: var(--color-ivory-faint);
		color: var(--color-ivory);
	}

	.button-row {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.error {
		font-size: 0.85rem;
		color: var(--color-risk);
		margin: -0.4rem 0 1rem;
	}
</style>
