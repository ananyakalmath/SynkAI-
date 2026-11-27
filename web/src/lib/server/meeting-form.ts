// Shared form parsing for the "schedule/edit meeting" form, used by both the
// calendar page's create action and the meeting detail page's update action.

import type { MeetingWriteData, Participant } from './api.js';

export const MEETING_TYPES = [
	'Standup',
	'Planning',
	'Review',
	'1:1',
	'All Hands',
	'Other'
] as const;

function asString(value: FormDataEntryValue | null): string {
	return typeof value === 'string' ? value.trim() : '';
}

/** Parses "Name, email@example.com" lines (one per line) into participants. */
export function parseParticipants(raw: string): Participant[] {
	const participants: Participant[] = [];
	for (const rawLine of raw.split('\n')) {
		const line = rawLine.trim();
		if (!line) continue;

		let name: string;
		let email: string;
		if (line.includes(',')) {
			const [first, ...rest] = line.split(',');
			name = first.trim();
			email = rest.join(',').trim();
		} else if (line.includes('<') && line.includes('>')) {
			const [first, rest] = line.split('<');
			name = first.trim();
			email = rest.replace('>', '').trim();
		} else {
			name = line;
			email = line;
		}
		participants.push({ name, email });
	}
	return participants;
}

export type MeetingFormError = { field?: string; message: string };

export function parseMeetingForm(form: FormData): MeetingWriteData | MeetingFormError {
	const title = asString(form.get('title'));
	if (!title) return { field: 'title', message: 'Title is required.' };

	const date = asString(form.get('date'));
	const startTime = asString(form.get('start_time'));
	const endTime = asString(form.get('end_time'));
	if (!date || !startTime || !endTime) {
		return { message: 'Date, start time, and end time are all required.' };
	}

	return {
		title,
		objective: asString(form.get('objective')) || null,
		meeting_type: asString(form.get('meeting_type')) || 'Other',
		date,
		start_time: startTime,
		end_time: endTime,
		timezone: asString(form.get('timezone')) || 'Asia/Kolkata',
		location: asString(form.get('location')) || null,
		participants: parseParticipants(asString(form.get('participants'))),
		previous_document_id: asString(form.get('previous_document_id')) || null,
		reminder_24h_enabled: form.get('reminder_24h_enabled') === 'on',
		reminder_1h_enabled: form.get('reminder_1h_enabled') === 'on'
	};
}
