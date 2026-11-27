<script lang="ts">
	import { resolve } from '$app/paths';
	import BoardroomBackdrop from '#lib/components/app/BoardroomBackdrop.svelte';
	import LoginForm from '#lib/components/app/LoginForm.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	// /signup has no actions of its own (see +page.server.ts) — its forms post to
	// /login's actions via LoginForm's `actionBase` prop, so SvelteKit can't infer
	// a concrete ActionData shape here. The runtime shape still matches /login's.
	const loginForm = $derived(
		form as
			{ stage?: string; email?: string; inviteCode?: string; error?: string } | null | undefined
	);
</script>

<svelte:head>
	<title>Create your boardroom — SynkAI</title>
</svelte:head>

<div class="stage">
	<BoardroomBackdrop />
	<div class="panel-wrap">
		{#if data.oauthError}
			<p class="oauth-error" role="alert">{data.oauthError}</p>
		{/if}
		<LoginForm
			heading="Create your boardroom."
			subheading="The same Google sign-in or emailed code — a workspace is set up the first time you continue."
			inviteCode={data.inviteCode}
			actionBase="/login"
			form={loginForm}
		/>
		<p class="switch-link">Already have a workspace? <a href={resolve('/login')}>Sign in →</a></p>
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
		max-width: 26rem;
	}

	.oauth-error {
		background: color-mix(in srgb, var(--color-risk) 15%, transparent);
		border: 1px solid color-mix(in srgb, var(--color-risk) 40%, transparent);
		color: var(--color-risk);
		border-radius: 8px;
		padding: 0.65rem 0.9rem;
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}

	.switch-link {
		text-align: center;
		margin-top: 1.25rem;
		font-size: 0.88rem;
		color: var(--color-ivory-dim);
	}

	.switch-link a {
		color: var(--color-brass);
		text-decoration: none;
	}

	.switch-link a:hover {
		color: var(--color-brass-bright);
	}
</style>
