<script lang="ts">
	import { resolve } from '$app/paths';
	import GlassPanel from '#lib/components/app/GlassPanel.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const firstName = $derived((data.user.full_name ?? data.user.email).split(' ')[0]);

	function greeting(): string {
		const hour = new Date().getHours();
		if (hour < 12) return 'Good morning';
		if (hour < 17) return 'Good afternoon';
		return 'Good evening';
	}

	function formatMeetingTime(date: string, start: string, end: string, timezone: string): string {
		return `${date} · ${start}–${end} (${timezone})`;
	}
</script>

<svelte:head>
	<title>Dashboard — SynkAI</title>
</svelte:head>

<header class="page-head">
	<p class="label label-signal">{data.user.workspace?.company_name ?? 'Workspace'}</p>
	<h1>{greeting()}, {firstName}.</h1>
</header>

<div class="grid">
	<GlassPanel>
		<div class="panel-head">
			<h2>Today &amp; upcoming</h2>
			<a href={resolve('/(app)/calendar')} class="quiet-link">Open calendar →</a>
		</div>

		{#if data.meetingsError}
			<p class="error-state" role="alert">{data.meetingsError}</p>
		{:else if data.todayMeetings.length === 0 && data.laterMeetings.length === 0}
			<p class="empty-state">Nothing scheduled. Plan your next meeting from the calendar.</p>
		{:else}
			{#if data.todayMeetings.length > 0}
				<p class="sublabel">Today</p>
				<ul class="meeting-list">
					{#each data.todayMeetings as meeting (meeting.id)}
						<li>
							<a href={resolve('/(app)/meetings/[id]', { id: meeting.id })} class="meeting-row">
								<span class="meeting-title">{meeting.title}</span>
								<span class="meeting-meta">
									{formatMeetingTime(
										meeting.date,
										meeting.start_time,
										meeting.end_time,
										meeting.timezone
									)}
								</span>
							</a>
						</li>
					{/each}
				</ul>
			{/if}
			{#if data.laterMeetings.length > 0}
				<p class="sublabel">Upcoming</p>
				<ul class="meeting-list">
					{#each data.laterMeetings as meeting (meeting.id)}
						<li>
							<a href={resolve('/(app)/meetings/[id]', { id: meeting.id })} class="meeting-row">
								<span class="meeting-title">{meeting.title}</span>
								<span class="meeting-meta">
									{formatMeetingTime(
										meeting.date,
										meeting.start_time,
										meeting.end_time,
										meeting.timezone
									)}
								</span>
							</a>
						</li>
					{/each}
				</ul>
			{/if}
		{/if}
	</GlassPanel>

	<GlassPanel>
		<h2>Quick actions</h2>
		<div class="action-list">
			<a href={resolve('/(app)/calendar')} class="action-button primary">Schedule a meeting</a>
			<a href={resolve('/(app)/ask')} class="action-button">Ask Synk</a>
			<a href={resolve('/(app)/documents')} class="action-button">Upload a document</a>
		</div>
	</GlassPanel>

	<GlassPanel>
		<h2>Pending action items</h2>
		<p class="empty-state">
			Run Meeting Analysis on a transcript and open items will appear here. (Documents &amp;
			analysis land in a later phase of this rebuild.)
		</p>
	</GlassPanel>

	<GlassPanel>
		<h2>Recent decisions</h2>
		<p class="empty-state">
			Decisions recorded during Meeting Analysis will appear here once Documents is wired up.
		</p>
	</GlassPanel>
</div>

<style>
	.page-head {
		margin-bottom: 2rem;
	}

	.page-head h1 {
		font-size: clamp(1.6rem, 2.8vw, 2.1rem);
		margin-top: 0.4rem;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1.25rem;
	}

	@media (max-width: 880px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}

	h2 {
		font-size: 1.05rem;
		font-weight: 500;
	}

	.panel-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 0.25rem;
	}

	.quiet-link {
		font-size: 0.82rem;
		color: var(--color-brass);
		text-decoration: none;
		white-space: nowrap;
	}

	.quiet-link:hover {
		color: var(--color-brass-bright);
	}

	.sublabel {
		font-size: 0.75rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-ivory-faint);
		margin: 1rem 0 0.5rem;
	}

	.meeting-list {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.meeting-row {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		padding: 0.6rem 0;
		border-bottom: 1px solid var(--color-graphite-2);
		text-decoration: none;
		color: var(--color-ivory);
	}

	.meeting-row:hover .meeting-title {
		color: var(--color-brass);
	}

	.meeting-title {
		font-size: 0.92rem;
	}

	.meeting-meta {
		font-family: var(--font-mono);
		font-size: 0.72rem;
		color: var(--color-ivory-faint);
	}

	.empty-state {
		color: var(--color-ivory-faint);
		font-size: 0.88rem;
		line-height: 1.6;
		margin-top: 0.6rem;
	}

	.error-state {
		color: var(--color-risk);
		font-size: 0.88rem;
		margin-top: 0.6rem;
	}

	.action-list {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		margin-top: 0.9rem;
	}

	.action-button {
		display: block;
		text-align: center;
		padding: 0.7rem 1rem;
		border-radius: 10px;
		border: 1px solid var(--color-graphite-2);
		color: var(--color-ivory);
		text-decoration: none;
		font-size: 0.88rem;
	}

	.action-button:hover {
		border-color: var(--color-ivory-faint);
	}

	.action-button.primary {
		background: var(--color-brass);
		color: var(--color-obsidian);
		border: none;
		font-weight: 600;
	}

	.action-button.primary:hover {
		background: var(--color-brass-bright);
	}
</style>
