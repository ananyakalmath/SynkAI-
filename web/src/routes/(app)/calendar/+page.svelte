<script lang="ts">
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';
	import { SvelteMap } from 'svelte/reactivity';
	import GlassPanel from '#lib/components/app/GlassPanel.svelte';
	import type { PageProps } from './$types';
	import type { ScheduledMeeting } from '#lib/server/api.js';

	let { data, form }: PageProps = $props();

	const MEETING_TYPES = ['Standup', 'Planning', 'Review', '1:1', 'All Hands', 'Other'];
	const TYPE_COLORS: Record<string, string> = {
		Standup: '#5B8DEF',
		Planning: '#8A63D2',
		Review: '#3FB68A',
		'1:1': '#E08E45',
		'All Hands': '#D1495B',
		Other: '#8A8A8A'
	};
	const MONTH_NAMES = [
		'January',
		'February',
		'March',
		'April',
		'May',
		'June',
		'July',
		'August',
		'September',
		'October',
		'November',
		'December'
	];
	const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

	let selectedDay = $state<number | null>(null);
	let showForm = $state(false);

	const byDay = $derived.by(() => {
		const map = new SvelteMap<number, ScheduledMeeting[]>();
		for (const meeting of data.meetings) {
			const day = Number(meeting.date.split('-')[2]);
			const existing = map.get(day);
			if (existing) existing.push(meeting);
			else map.set(day, [meeting]);
		}
		return map;
	});

	// A Monday-first grid of the month, padded with 0s for days outside it —
	// the same shape as Python's calendar.monthcalendar().
	const weeks = $derived.by(() => {
		const { year, month } = data;
		const daysInMonth = new Date(year, month, 0).getDate();
		const firstWeekday = (new Date(year, month - 1, 1).getDay() + 6) % 7; // 0 = Monday

		const days: number[] = Array.from({ length: firstWeekday }, () => 0);
		for (let day = 1; day <= daysInMonth; day++) days.push(day);
		while (days.length % 7 !== 0) days.push(0);

		const result: number[][] = [];
		for (let i = 0; i < days.length; i += 7) result.push(days.slice(i, i + 7));
		return result;
	});

	function prevMonthHref(): string {
		const { year, month } = data;
		return month === 1
			? resolve(`/(app)/calendar?year=${year - 1}&month=12`)
			: resolve(`/(app)/calendar?year=${year}&month=${month - 1}`);
	}

	function nextMonthHref(): string {
		const { year, month } = data;
		return month === 12
			? resolve(`/(app)/calendar?year=${year + 1}&month=1`)
			: resolve(`/(app)/calendar?year=${year}&month=${month + 1}`);
	}

	function selectedMeetings(): ScheduledMeeting[] {
		if (selectedDay === null) return [];
		return byDay.get(selectedDay) ?? [];
	}

	function formatRange(meeting: ScheduledMeeting): string {
		return `${meeting.start_time}–${meeting.end_time} (${meeting.timezone})`;
	}

	let submitting = $state(false);
</script>

<svelte:head>
	<title>Calendar — SynkAI</title>
</svelte:head>

<header class="page-head">
	<p class="label label-signal">Workspace</p>
	<h1>Calendar</h1>
</header>

{#if data.calendarConnected}
	<p class="notice success">Google Calendar connected.</p>
{/if}
{#if data.calendarError}
	<p class="notice error">{data.calendarError}</p>
{/if}

<GlassPanel tight>
	<div class="google-row">
		<div>
			<p class="google-label">Google Calendar</p>
			<p class="google-status">
				{data.googleConnected
					? 'Connected — your scheduled meetings sync as real Calendar events with a Meet link.'
					: 'Not connected — invites are emailed with a standard .ics attachment instead.'}
			</p>
		</div>
		{#if data.googleConnected}
			<form method="POST" action="?/disconnectGoogle" use:enhance>
				<button type="submit" class="ghost-button">Disconnect</button>
			</form>
		{:else}
			<a href={resolve('/(app)/calendar/connect-google')} class="ghost-button">
				Connect Google Calendar
			</a>
		{/if}
	</div>
</GlassPanel>

<div class="layout">
	<GlassPanel>
		<div class="calendar-head">
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- prevMonthHref() wraps resolve() internally -->
			<a href={prevMonthHref()} class="nav-arrow" aria-label="Previous month">←</a>
			<h2>{MONTH_NAMES[data.month - 1]} {data.year}</h2>
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- nextMonthHref() wraps resolve() internally -->
			<a href={nextMonthHref()} class="nav-arrow" aria-label="Next month">→</a>
		</div>

		{#if data.meetingsError}
			<p class="notice error">{data.meetingsError}</p>
		{/if}

		<div class="weekday-row">
			{#each WEEKDAY_LABELS as label (label)}
				<span class="weekday">{label}</span>
			{/each}
		</div>

		{#each weeks as week, weekIndex (weekIndex)}
			<div class="week-row">
				{#each week as day, dayIndex (dayIndex)}
					{#if day === 0}
						<div class="day-cell empty"></div>
					{:else}
						{@const dayMeetings = byDay.get(day) ?? []}
						<button
							type="button"
							class="day-cell"
							class:selected={selectedDay === day}
							onclick={() => {
								selectedDay = day;
								showForm = false;
							}}
						>
							<span class="day-number">{day}</span>
							{#if dayMeetings.length > 0}
								<span class="day-dots">
									{#each dayMeetings.slice(0, 4) as meeting (meeting.id)}
										<span
											class="dot"
											style={`background:${TYPE_COLORS[meeting.meeting_type] ?? TYPE_COLORS.Other}`}
										></span>
									{/each}
								</span>
								<span class="day-title">{dayMeetings[0].title}</span>
							{/if}
						</button>
					{/if}
				{/each}
			</div>
		{/each}
	</GlassPanel>

	<div class="side-column">
		<GlassPanel>
			{#if showForm}
				<div class="panel-head">
					<h2>Schedule a meeting</h2>
					<button type="button" class="quiet-link" onclick={() => (showForm = false)}>
						Cancel
					</button>
				</div>

				<form
					method="POST"
					action="?/createMeeting"
					use:enhance={() => {
						submitting = true;
						return async ({ update }) => {
							await update();
							submitting = false;
						};
					}}
				>
					<label class="field-label" for="title">Title</label>
					<input id="title" name="title" required class="text-field" />

					<label class="field-label" for="objective">Objective</label>
					<textarea id="objective" name="objective" class="text-field" rows="2"></textarea>

					<label class="field-label" for="meeting_type">Meeting type</label>
					<select id="meeting_type" name="meeting_type" class="text-field">
						{#each MEETING_TYPES as type (type)}
							<option value={type}>{type}</option>
						{/each}
					</select>

					<div class="field-grid">
						<div>
							<label class="field-label" for="date">Date</label>
							<input id="date" name="date" type="date" required class="text-field" />
						</div>
						<div>
							<label class="field-label" for="start_time">Start</label>
							<input id="start_time" name="start_time" type="time" required class="text-field" />
						</div>
						<div>
							<label class="field-label" for="end_time">End</label>
							<input id="end_time" name="end_time" type="time" required class="text-field" />
						</div>
					</div>

					<label class="field-label" for="timezone">Timezone (IANA)</label>
					<input id="timezone" name="timezone" value="Asia/Kolkata" class="text-field" />

					<label class="field-label" for="location">Location or meeting link</label>
					<input id="location" name="location" class="text-field" />

					<label class="field-label" for="participants">
						Participants — one per line: "Name, email@example.com"
					</label>
					<textarea id="participants" name="participants" class="text-field" rows="3"></textarea>

					<label class="field-label" for="previous_document_id">
						Previous meeting's document ID (optional)
					</label>
					<input id="previous_document_id" name="previous_document_id" class="text-field" />

					<label class="checkbox-row">
						<input type="checkbox" name="reminder_24h_enabled" checked />
						Send a 24h reminder
					</label>
					<label class="checkbox-row">
						<input type="checkbox" name="reminder_1h_enabled" checked />
						Send a 1h reminder
					</label>

					{#if form?.error}
						<p class="notice error">{form.error}</p>
					{/if}

					<button type="submit" class="primary-button" disabled={submitting}>
						{submitting ? 'Scheduling…' : 'Schedule meeting'}
					</button>
				</form>
			{:else if form?.created}
				{@const createdMeeting = form.created.meeting}
				{@const failed = form.created.invite_results.filter(
					(r: { success: boolean }) => !r.success
				)}
				<h2>Meeting scheduled</h2>
				{#if createdMeeting.google_meet_link}
					<p class="notice success">
						Synced to Google Calendar — Meet link: {createdMeeting.google_meet_link}
					</p>
				{:else if failed.length > 0}
					<p class="notice error">
						Scheduled, but the invite failed for: {failed
							.map((r: { email: string }) => r.email)
							.join(', ')}
					</p>
				{:else}
					<p class="notice success">Invites emailed to every participant.</p>
				{/if}
				<button type="button" class="primary-button" onclick={() => (showForm = true)}>
					Schedule another
				</button>
			{:else if selectedDay !== null}
				<div class="panel-head">
					<h2>
						{data.year}-{String(data.month).padStart(2, '0')}-{String(selectedDay).padStart(2, '0')}
					</h2>
					<button type="button" class="quiet-link" onclick={() => (showForm = true)}>
						+ Schedule
					</button>
				</div>

				{#if selectedMeetings().length === 0}
					<p class="empty-state">No meetings scheduled. Click "+ Schedule" to plan one.</p>
				{:else}
					{#each selectedMeetings() as meeting (meeting.id)}
						<a href={resolve('/(app)/meetings/[id]', { id: meeting.id })} class="meeting-card">
							<div class="meeting-card-head">
								<span
									class="type-dot"
									style={`background:${TYPE_COLORS[meeting.meeting_type] ?? TYPE_COLORS.Other}`}
								></span>
								<strong>{meeting.title}</strong>
								{#if meeting.status === 'cancelled'}
									<span class="status-tag">Cancelled</span>
								{/if}
							</div>
							<p class="meeting-meta">{formatRange(meeting)}</p>
							{#if meeting.location}
								<p class="meeting-meta">{meeting.location}</p>
							{/if}
						</a>
					{/each}
				{/if}
			{:else}
				<h2>Pick a day</h2>
				<p class="empty-state">
					Click a day on the calendar to see what's scheduled, or schedule a new meeting.
				</p>
				<button type="button" class="primary-button" onclick={() => (showForm = true)}>
					Schedule a meeting
				</button>
			{/if}
		</GlassPanel>
	</div>
</div>

<style>
	.page-head {
		margin-bottom: 1.5rem;
	}

	.page-head h1 {
		font-size: clamp(1.6rem, 2.8vw, 2.1rem);
		margin-top: 0.4rem;
	}

	.notice {
		border-radius: 8px;
		padding: 0.6rem 0.9rem;
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}

	.notice.success {
		color: var(--color-good);
		background: color-mix(in srgb, var(--color-good) 12%, transparent);
		border: 1px solid color-mix(in srgb, var(--color-good) 30%, transparent);
	}

	.notice.error {
		color: var(--color-risk);
		background: color-mix(in srgb, var(--color-risk) 12%, transparent);
		border: 1px solid color-mix(in srgb, var(--color-risk) 30%, transparent);
	}

	.google-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.google-label {
		font-size: 0.8rem;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--color-ivory-faint);
		margin-bottom: 0.3rem;
	}

	.google-status {
		font-size: 0.88rem;
		color: var(--color-ivory-dim);
		max-width: 36rem;
	}

	.layout {
		display: grid;
		grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
		gap: 1.25rem;
		margin-top: 1.25rem;
	}

	@media (max-width: 960px) {
		.layout {
			grid-template-columns: 1fr;
		}
	}

	.calendar-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}

	.calendar-head h2 {
		font-size: 1.1rem;
		font-weight: 500;
	}

	.nav-arrow {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		border: 1px solid var(--color-graphite-2);
		color: var(--color-ivory);
		text-decoration: none;
	}

	.nav-arrow:hover {
		border-color: var(--color-brass);
		color: var(--color-brass);
	}

	.weekday-row,
	.week-row {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 0.4rem;
	}

	.weekday {
		text-align: center;
		font-size: 0.72rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--color-ivory-faint);
		padding-bottom: 0.4rem;
	}

	.week-row {
		margin-bottom: 0.4rem;
	}

	.day-cell {
		min-height: 4.2rem;
		border-radius: 8px;
		border: 1px solid var(--color-graphite-2);
		background: transparent;
		color: var(--color-ivory);
		text-align: left;
		padding: 0.4rem;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		cursor: pointer;
		overflow: hidden;
	}

	.day-cell.empty {
		border: none;
		cursor: default;
	}

	.day-cell:not(.empty):hover {
		border-color: var(--color-ivory-faint);
	}

	.day-cell.selected {
		border-color: var(--color-brass);
		background: color-mix(in srgb, var(--color-brass) 10%, transparent);
	}

	.day-number {
		font-size: 0.8rem;
		color: var(--color-ivory-dim);
	}

	.day-dots {
		display: flex;
		gap: 0.2rem;
	}

	.dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
	}

	.day-title {
		font-size: 0.68rem;
		color: var(--color-ivory-faint);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.side-column {
		min-width: 0;
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
		margin-bottom: 0.9rem;
	}

	.quiet-link {
		font-size: 0.82rem;
		color: var(--color-brass);
		background: none;
		border: none;
		cursor: pointer;
		white-space: nowrap;
	}

	.quiet-link:hover {
		color: var(--color-brass-bright);
	}

	.empty-state {
		color: var(--color-ivory-faint);
		font-size: 0.88rem;
		line-height: 1.6;
		margin-bottom: 1rem;
	}

	.field-label {
		display: block;
		font-size: 0.75rem;
		letter-spacing: 0.02em;
		color: var(--color-ivory-dim);
		margin-bottom: 0.35rem;
		margin-top: 0.8rem;
	}

	.text-field {
		width: 100%;
		background: var(--color-obsidian);
		border: 1px solid var(--color-graphite-2);
		border-radius: 8px;
		padding: 0.55rem 0.7rem;
		color: var(--color-ivory);
		font-size: 0.88rem;
		font-family: inherit;
	}

	.text-field:focus {
		border-color: var(--color-brass);
		outline: none;
	}

	.field-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.6rem;
	}

	.checkbox-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.85rem;
		color: var(--color-ivory-dim);
		margin-top: 0.7rem;
	}

	.primary-button {
		width: 100%;
		padding: 0.7rem 1rem;
		border-radius: 10px;
		border: none;
		background: var(--color-brass);
		color: var(--color-obsidian);
		font-weight: 600;
		font-size: 0.88rem;
		margin-top: 1.1rem;
	}

	.primary-button:hover:not(:disabled) {
		background: var(--color-brass-bright);
	}

	.primary-button:disabled {
		opacity: 0.6;
	}

	.ghost-button {
		padding: 0.55rem 0.9rem;
		border-radius: 8px;
		border: 1px solid var(--color-graphite-2);
		background: transparent;
		color: var(--color-ivory);
		font-size: 0.82rem;
		text-decoration: none;
		white-space: nowrap;
	}

	.ghost-button:hover {
		border-color: var(--color-ivory-faint);
	}

	.meeting-card {
		display: block;
		border: 1px solid var(--color-graphite-2);
		border-radius: 10px;
		padding: 0.75rem 0.9rem;
		margin-bottom: 0.6rem;
		text-decoration: none;
		color: var(--color-ivory);
	}

	.meeting-card:hover {
		border-color: var(--color-brass);
	}

	.meeting-card-head {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.type-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.status-tag {
		font-size: 0.68rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--color-ivory-faint);
	}

	.meeting-meta {
		font-family: var(--font-mono);
		font-size: 0.74rem;
		color: var(--color-ivory-faint);
		margin-top: 0.3rem;
	}
</style>
