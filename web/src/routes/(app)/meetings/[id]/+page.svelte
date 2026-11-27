<script lang="ts">
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';
	import GlassPanel from '#lib/components/app/GlassPanel.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	const meeting = $derived(form?.updated?.meeting ?? data.meeting);

	const MEETING_TYPES = ['Standup', 'Planning', 'Review', '1:1', 'All Hands', 'Other'];

	let editing = $state(false);
	let submitting = $state(false);

	function participantsText(): string {
		return meeting.participants.map((p) => `${p.name}, ${p.email}`).join('\n');
	}
</script>

<svelte:head>
	<title>{meeting.title} — SynkAI</title>
</svelte:head>

<header class="page-head">
	<a href={resolve('/(app)/calendar')} class="back-link">← Calendar</a>
	<h1>{meeting.title}</h1>
	<p class="meta-line">
		{meeting.date} · {meeting.start_time}–{meeting.end_time} ({meeting.timezone})
		{#if meeting.status === 'cancelled'}
			<span class="status-tag">Cancelled</span>
		{/if}
	</p>
</header>

{#if form?.error}
	<p class="notice error">{form.error}</p>
{/if}
{#if meeting.calendar_sync_error}
	<p class="notice error">Google Calendar sync issue: {meeting.calendar_sync_error}</p>
{/if}
{#if form?.updated}
	<p class="notice success">Meeting updated and participants notified.</p>
{/if}

<div class="layout">
	<GlassPanel>
		{#if editing}
			<div class="panel-head">
				<h2>Edit meeting</h2>
				<button type="button" class="quiet-link" onclick={() => (editing = false)}>
					Cancel edit
				</button>
			</div>

			<form
				method="POST"
				action="?/update"
				use:enhance={() => {
					submitting = true;
					return async ({ update }) => {
						await update();
						submitting = false;
						editing = false;
					};
				}}
			>
				<label class="field-label" for="title">Title</label>
				<input id="title" name="title" required class="text-field" value={meeting.title} />

				<label class="field-label" for="objective">Objective</label>
				<textarea id="objective" name="objective" class="text-field" rows="2"
					>{meeting.objective ?? ''}</textarea
				>

				<label class="field-label" for="meeting_type">Meeting type</label>
				<select
					id="meeting_type"
					name="meeting_type"
					class="text-field"
					value={meeting.meeting_type}
				>
					{#each MEETING_TYPES as type (type)}
						<option value={type} selected={type === meeting.meeting_type}>{type}</option>
					{/each}
				</select>

				<div class="field-grid">
					<div>
						<label class="field-label" for="date">Date</label>
						<input
							id="date"
							name="date"
							type="date"
							required
							class="text-field"
							value={meeting.date}
						/>
					</div>
					<div>
						<label class="field-label" for="start_time">Start</label>
						<input
							id="start_time"
							name="start_time"
							type="time"
							required
							class="text-field"
							value={meeting.start_time}
						/>
					</div>
					<div>
						<label class="field-label" for="end_time">End</label>
						<input
							id="end_time"
							name="end_time"
							type="time"
							required
							class="text-field"
							value={meeting.end_time}
						/>
					</div>
				</div>

				<label class="field-label" for="timezone">Timezone (IANA)</label>
				<input id="timezone" name="timezone" class="text-field" value={meeting.timezone} />

				<label class="field-label" for="location">Location or meeting link</label>
				<input id="location" name="location" class="text-field" value={meeting.location ?? ''} />

				<label class="field-label" for="participants">
					Participants — one per line: "Name, email@example.com"
				</label>
				<textarea id="participants" name="participants" class="text-field" rows="3"
					>{participantsText()}</textarea
				>

				<label class="field-label" for="previous_document_id">
					Previous meeting's document ID (optional)
				</label>
				<input
					id="previous_document_id"
					name="previous_document_id"
					class="text-field"
					value={meeting.previous_document_id ?? ''}
				/>

				<label class="checkbox-row">
					<input
						type="checkbox"
						name="reminder_24h_enabled"
						checked={meeting.reminder_24h_enabled}
					/>
					Send a 24h reminder
				</label>
				<label class="checkbox-row">
					<input type="checkbox" name="reminder_1h_enabled" checked={meeting.reminder_1h_enabled} />
					Send a 1h reminder
				</label>

				<button type="submit" class="primary-button" disabled={submitting}>
					{submitting ? 'Saving…' : 'Save changes'}
				</button>
			</form>
		{:else}
			<div class="panel-head">
				<h2>Details</h2>
				{#if meeting.status !== 'cancelled'}
					<button type="button" class="quiet-link" onclick={() => (editing = true)}>Edit</button>
				{/if}
			</div>

			{#if meeting.objective}
				<p class="detail-row"><span class="detail-label">Objective</span>{meeting.objective}</p>
			{/if}
			<p class="detail-row">
				<span class="detail-label">Organiser</span>{meeting.organiser.name ??
					meeting.organiser.email}
			</p>
			{#if meeting.location}
				<p class="detail-row"><span class="detail-label">Location</span>{meeting.location}</p>
			{/if}
			{#if meeting.google_meet_link}
				<p class="detail-row">
					<span class="detail-label">Google Meet</span>
					<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- external meet.google.com URL, not an app route -->
					<a href={meeting.google_meet_link} target="_blank" rel="noopener">
						{meeting.google_meet_link}
					</a>
				</p>
			{/if}

			<p class="detail-label section-label">Participants</p>
			{#if meeting.participants.length === 0}
				<p class="empty-state">No participants added.</p>
			{:else}
				<ul class="participant-list">
					{#each meeting.participants as p (p.email)}
						<li>{p.name} <span class="meta-faint">({p.email})</span></li>
					{/each}
				</ul>
			{/if}

			{#if meeting.document_ids.length > 0}
				<p class="detail-row">
					<span class="detail-label">Attached documents</span>{meeting.document_ids.join(', ')}
				</p>
			{/if}

			{#if meeting.status !== 'cancelled'}
				<form
					method="POST"
					action="?/cancel"
					use:enhance={() => {
						submitting = true;
						return async ({ update }) => {
							await update();
							submitting = false;
						};
					}}
				>
					<button type="submit" class="danger-button" disabled={submitting}>
						{submitting ? 'Cancelling…' : 'Cancel meeting'}
					</button>
				</form>
			{/if}
		{/if}
	</GlassPanel>
</div>

<style>
	.page-head {
		margin-bottom: 1.5rem;
	}

	.back-link {
		font-size: 0.82rem;
		color: var(--color-ivory-faint);
		text-decoration: none;
	}

	.back-link:hover {
		color: var(--color-ivory);
	}

	.page-head h1 {
		font-size: clamp(1.5rem, 2.6vw, 2rem);
		margin-top: 0.5rem;
	}

	.meta-line {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--color-ivory-faint);
		margin-top: 0.4rem;
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.status-tag {
		font-family: var(--font-sans);
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--color-risk);
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

	.layout {
		max-width: 38rem;
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
	}

	.quiet-link:hover {
		color: var(--color-brass-bright);
	}

	.detail-row {
		font-size: 0.9rem;
		color: var(--color-ivory);
		margin-bottom: 0.7rem;
		line-height: 1.5;
	}

	.detail-row a {
		color: var(--color-signal);
	}

	.detail-label {
		display: block;
		font-size: 0.72rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--color-ivory-faint);
		margin-bottom: 0.2rem;
	}

	.section-label {
		margin-top: 1.1rem;
	}

	.empty-state {
		color: var(--color-ivory-faint);
		font-size: 0.85rem;
	}

	.participant-list {
		list-style: none;
		margin: 0 0 0.5rem;
		padding: 0;
		font-size: 0.88rem;
		color: var(--color-ivory);
	}

	.participant-list li {
		padding: 0.3rem 0;
	}

	.meta-faint {
		color: var(--color-ivory-faint);
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

	.danger-button {
		margin-top: 1.25rem;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		border: 1px solid color-mix(in srgb, var(--color-risk) 50%, transparent);
		background: transparent;
		color: var(--color-risk);
		font-size: 0.85rem;
	}

	.danger-button:hover:not(:disabled) {
		background: color-mix(in srgb, var(--color-risk) 12%, transparent);
	}

	.danger-button:disabled {
		opacity: 0.6;
	}
</style>
