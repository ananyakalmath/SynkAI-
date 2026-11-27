<script lang="ts">
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';
	import GlassPanel from './GlassPanel.svelte';

	type LoginActionData =
		{ stage?: string; email?: string; inviteCode?: string; error?: string } | null | undefined;

	let {
		heading,
		subheading,
		inviteCode = null,
		actionBase = '',
		form
	}: {
		heading: string;
		subheading: string;
		inviteCode?: string | null;
		/** Lets /signup post to /login's actions instead of duplicating server logic. */
		actionBase?: string;
		form: LoginActionData;
	} = $props();

	const effectiveInvite = $derived(form?.inviteCode ?? inviteCode ?? '');
	const stage = $derived(form?.stage === 'verify' ? 'verify' : 'request');
	const email = $derived(form?.email ?? '');

	let submitting = $state(false);
</script>

<GlassPanel glow="brass">
	<p class="label label-signal">SynkAI</p>
	<h1>{heading}</h1>
	<p class="subheading">{subheading}</p>

	{#if effectiveInvite}
		<p class="invite-note">You're signing in to accept a workspace invite.</p>
	{/if}

	<a
		class="google-button"
		href={effectiveInvite
			? resolve(`/login/google?invite=${encodeURIComponent(effectiveInvite)}`)
			: resolve('/login/google')}
	>
		<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
			<path
				fill="#4285F4"
				d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84c-.21 1.13-.84 2.07-1.8 2.71v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.61z"
			/>
			<path
				fill="#34A853"
				d="M9 18c2.43 0 4.47-.8 5.96-2.19l-2.92-2.26c-.81.55-1.84.87-3.04.87-2.34 0-4.33-1.58-5.04-3.71H.96v2.33C2.44 15.98 5.48 18 9 18z"
			/>
			<path
				fill="#FBBC05"
				d="M3.96 10.71c-.18-.55-.28-1.13-.28-1.71s.1-1.16.28-1.71V4.96H.96A8.997 8.997 0 0 0 0 9c0 1.45.35 2.82.96 4.04l3-2.33z"
			/>
			<path
				fill="#EA4335"
				d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.59C13.46.89 11.43 0 9 0 5.48 0 2.44 2.02.96 4.96l3 2.33C4.67 5.16 6.66 3.58 9 3.58z"
			/>
		</svg>
		Continue with Google
	</a>

	<div class="divider"><span>or</span></div>

	{#if stage === 'request'}
		<form
			method="POST"
			action={`${actionBase}?/requestCode`}
			use:enhance={() => {
				submitting = true;
				return async ({ update }) => {
					await update();
					submitting = false;
				};
			}}
		>
			<input type="hidden" name="invite_code" value={effectiveInvite} />
			<label class="field-label" for="login-email">Work email</label>
			<input
				id="login-email"
				name="email"
				type="email"
				required
				placeholder="you@company.com"
				value={email}
				class="text-field"
			/>
			{#if form?.error}
				<p class="error" role="alert">{form.error}</p>
			{/if}
			<button type="submit" class="primary-button" disabled={submitting}>
				{submitting ? 'Sending…' : 'Send sign-in code'}
			</button>
		</form>
	{:else}
		<p class="sent-note">
			We sent a 6-digit code to <strong>{email}</strong>. It expires in 10 minutes.
		</p>
		<form
			method="POST"
			action={`${actionBase}?/verifyCode`}
			use:enhance={() => {
				submitting = true;
				return async ({ update }) => {
					await update();
					submitting = false;
				};
			}}
		>
			<input type="hidden" name="email" value={email} />
			<input type="hidden" name="invite_code" value={effectiveInvite} />
			<label class="field-label" for="login-code">Code</label>
			<input
				id="login-code"
				name="code"
				inputmode="numeric"
				maxlength="6"
				required
				class="text-field code-field"
			/>
			{#if form?.error}
				<p class="error" role="alert">{form.error}</p>
			{/if}
			<div class="button-row">
				<button type="submit" class="primary-button" disabled={submitting}>
					{submitting ? 'Verifying…' : 'Verify and sign in'}
				</button>
				<button type="submit" formaction={`${actionBase}?/restart`} class="ghost-button">
					Use a different email
				</button>
			</div>
		</form>
	{/if}
</GlassPanel>

<style>
	h1 {
		font-size: clamp(1.5rem, 2.6vw, 2rem);
		margin: 0.4rem 0 0.6rem;
	}

	.subheading {
		color: var(--color-ivory-dim);
		font-size: 0.95rem;
		margin-bottom: 1.5rem;
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

	.google-button {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.6rem;
		width: 100%;
		padding: 0.75rem 1rem;
		border-radius: 10px;
		background: var(--color-ivory);
		color: var(--color-obsidian);
		font-weight: 600;
		font-size: 0.92rem;
		text-decoration: none;
		transition: transform 0.2s ease;
	}

	.google-button:hover {
		transform: translateY(-1px);
	}

	.divider {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin: 1.25rem 0;
		color: var(--color-ivory-faint);
		font-size: 0.8rem;
	}

	.divider::before,
	.divider::after {
		content: '';
		flex: 1;
		height: 1px;
		background: var(--color-graphite-2);
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
		transition: border-color 0.2s ease;
	}

	.text-field:focus {
		border-color: var(--color-brass);
		outline: none;
	}

	.code-field {
		letter-spacing: 0.3em;
		font-family: var(--font-mono);
		font-size: 1.1rem;
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
		transition: background 0.2s ease;
	}

	.primary-button:hover:not(:disabled) {
		background: var(--color-brass-bright);
	}

	.primary-button:disabled {
		opacity: 0.6;
		cursor: default;
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

	.sent-note {
		font-size: 0.88rem;
		color: var(--color-ivory-dim);
		margin-bottom: 1.1rem;
	}

	.error {
		font-size: 0.85rem;
		color: var(--color-risk);
		margin: -0.4rem 0 1rem;
	}
</style>
