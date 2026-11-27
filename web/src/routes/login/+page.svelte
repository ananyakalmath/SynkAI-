<script lang="ts">
	import { resolve } from '$app/paths';
	import BoardroomBackdrop from '#lib/components/app/BoardroomBackdrop.svelte';
	import LoginForm from '#lib/components/app/LoginForm.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();
</script>

<svelte:head>
	<title>Sign in — SynkAI</title>
</svelte:head>

<div class="stage">
	<BoardroomBackdrop />
	<div class="panel-wrap">
		{#if data.oauthError}
			<p class="oauth-error" role="alert">{data.oauthError}</p>
		{/if}
		<LoginForm
			heading="Welcome back."
			subheading="Sign in with Google, or with a code sent to your work email. No passwords."
			inviteCode={data.inviteCode}
			{form}
		/>
		<p class="switch-link">
			New to SynkAI? <a href={resolve('/signup')}>Create your boardroom →</a>
		</p>
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
