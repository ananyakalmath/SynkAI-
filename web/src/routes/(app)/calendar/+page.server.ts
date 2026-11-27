import { fail } from '@sveltejs/kit';
import {
	ApiError,
	createScheduledMeeting,
	googleCalendarStatus,
	googleCalendarDisconnect,
	listScheduledMeetings
} from '#lib/server/api.js';
import { parseMeetingForm } from '#lib/server/meeting-form.js';
import { getSessionToken } from '#lib/server/session.js';
import type { Actions, PageServerLoad } from './$types';

function clampMonth(value: number): number {
	return Math.min(12, Math.max(1, value));
}

export const load: PageServerLoad = async ({ cookies, url }) => {
	const token = getSessionToken(cookies) as string; // guaranteed by (app)/+layout.server.ts
	const now = new Date();

	const year = Number(url.searchParams.get('year')) || now.getFullYear();
	const month = clampMonth(Number(url.searchParams.get('month')) || now.getMonth() + 1);

	let meetings: Awaited<ReturnType<typeof listScheduledMeetings>>['meetings'] = [];
	let meetingsError: string | null = null;
	try {
		meetings = (await listScheduledMeetings(token, year, month)).meetings;
	} catch (error) {
		meetingsError = error instanceof ApiError ? error.message : 'Could not load meetings.';
	}

	let googleConnected = false;
	try {
		googleConnected = (await googleCalendarStatus(token)).connected;
	} catch {
		// Non-critical for rendering the calendar — the schedule form still works
		// via the SMTP + .ics fallback either way.
	}

	return {
		year,
		month,
		meetings,
		meetingsError,
		googleConnected,
		calendarConnected: url.searchParams.get('calendar_connected') === '1',
		calendarError: url.searchParams.get('calendar_error')
	};
};

export const actions: Actions = {
	createMeeting: async ({ request, cookies }) => {
		const token = getSessionToken(cookies) as string;
		const form = await request.formData();
		const parsed = parseMeetingForm(form);
		if ('message' in parsed) {
			return fail(400, { error: parsed.message });
		}

		try {
			const result = await createScheduledMeeting(token, parsed);
			return { created: result };
		} catch (error) {
			const message = error instanceof ApiError ? error.message : 'Could not schedule the meeting.';
			return fail(error instanceof ApiError ? error.status : 502, { error: message });
		}
	},

	disconnectGoogle: async ({ cookies }) => {
		const token = getSessionToken(cookies) as string;
		await googleCalendarDisconnect(token);
		return { disconnected: true };
	}
};
