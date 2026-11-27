<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import type { UserProfile } from '#lib/server/api.js';

	let { user }: { user: UserProfile } = $props();

	const NAV_ITEMS = [
		{ href: resolve('/(app)/dashboard'), label: 'Dashboard', icon: 'grid' },
		{ href: resolve('/(app)/calendar'), label: 'Calendar', icon: 'calendar' },
		{ href: resolve('/(app)/documents'), label: 'Documents', icon: 'folder' },
		{ href: resolve('/(app)/ask'), label: 'Ask Synk', icon: 'chat' },
		{ href: resolve('/(app)/profile'), label: 'Profile', icon: 'user' }
	];

	const initials = $derived(
		(user.full_name ?? user.email)
			.split(' ')
			.slice(0, 2)
			.map((part) => part[0])
			.join('')
			.toUpperCase()
	);
</script>

{#snippet icon(name: string)}
	{#if name === 'grid'}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
			<rect x="3" y="3" width="8" height="8" rx="1.5" /><rect
				x="13"
				y="3"
				width="8"
				height="8"
				rx="1.5"
			/><rect x="3" y="13" width="8" height="8" rx="1.5" /><rect
				x="13"
				y="13"
				width="8"
				height="8"
				rx="1.5"
			/>
		</svg>
	{:else if name === 'calendar'}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
			<rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 9h18M8 3v4M16 3v4" />
		</svg>
	{:else if name === 'folder'}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
			<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
		</svg>
	{:else if name === 'chat'}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
			<path d="M21 11.5a8.5 8.5 0 1 1-3.8-7.07M21 11.5 17 15l.5-4.5" /><path
				d="M3 11.5A8.5 8.5 0 0 1 11.5 3"
			/>
		</svg>
	{:else}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
			<circle cx="12" cy="8" r="4" /><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
		</svg>
	{/if}
{/snippet}

<nav class="sidebar" aria-label="Main">
	<div class="brand">
		<span class="label label-signal">SynkAI</span>
	</div>

	<ul class="nav-list">
		{#each NAV_ITEMS as item (item.href)}
			<li>
				<a
					href={item.href}
					class="nav-link"
					aria-current={page.url.pathname.startsWith(item.href) ? 'page' : undefined}
				>
					<span class="nav-icon">{@render icon(item.icon)}</span>
					{item.label}
				</a>
			</li>
		{/each}
	</ul>

	<div class="sidebar-footer">
		<div class="user-chip">
			<span class="avatar">{initials}</span>
			<span class="user-text">
				<span class="user-name">{user.full_name ?? user.email}</span>
				<span class="user-company">{user.workspace?.company_name ?? ''}</span>
			</span>
		</div>
		<form method="POST" action="/logout">
			<button type="submit" class="signout-button">Sign out</button>
		</form>
	</div>
</nav>

<style>
	.sidebar {
		display: flex;
		flex-direction: column;
		height: 100%;
		padding: 1.5rem 1rem;
		border-right: 1px solid var(--color-graphite-2);
		background: var(--color-obsidian-2);
	}

	.brand {
		padding: 0 0.5rem 1.5rem;
	}

	.nav-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		flex: 1;
	}

	.nav-link {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.65rem 0.75rem;
		border-radius: 10px;
		color: var(--color-ivory-dim);
		text-decoration: none;
		font-size: 0.9rem;
		transition:
			background 0.2s ease,
			color 0.2s ease;
	}

	.nav-link:hover {
		background: var(--color-graphite);
		color: var(--color-ivory);
	}

	.nav-link[aria-current='page'] {
		background: var(--color-graphite);
		color: var(--color-ivory);
	}

	.nav-link[aria-current='page'] .nav-icon {
		color: var(--color-brass);
	}

	.nav-icon {
		width: 18px;
		height: 18px;
		flex-shrink: 0;
	}

	.nav-icon svg {
		width: 100%;
		height: 100%;
	}

	.sidebar-footer {
		border-top: 1px solid var(--color-graphite-2);
		padding-top: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.user-chip {
		display: flex;
		align-items: center;
		gap: 0.65rem;
		padding: 0 0.25rem;
	}

	.avatar {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		background: var(--color-graphite);
		color: var(--color-brass);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		font-weight: 600;
		flex-shrink: 0;
	}

	.user-text {
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.user-name {
		font-size: 0.85rem;
		color: var(--color-ivory);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.user-company {
		font-size: 0.75rem;
		color: var(--color-ivory-faint);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.signout-button {
		width: 100%;
		padding: 0.55rem 0.75rem;
		border-radius: 8px;
		border: 1px solid var(--color-graphite-2);
		background: transparent;
		color: var(--color-ivory-dim);
		font-size: 0.82rem;
	}

	.signout-button:hover {
		border-color: var(--color-ivory-faint);
		color: var(--color-ivory);
	}
</style>
