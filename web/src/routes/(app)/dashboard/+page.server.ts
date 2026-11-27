import { ApiError, listScheduledMeetings, type ScheduledMeeting } from '#lib/server/api.js';
import { getSessionToken } from '#lib/server/session.js';
import type { PageServerLoad } from './$types';

function todayIso(): string {
	return new Date().toISOString().slice(0, 10);
}

export const load: PageServerLoad = async ({ cookies }) => {
	const token = getSessionToken(cookies) as string; // guaranteed by (app)/+layout.server.ts
	const now = new Date();

	let meetings: ScheduledMeeting[] = [];
	let meetingsError: string | null = null;

	try {
		// The current month covers "today"; pull next month too so "upcoming" still
		// shows something meaningful in the last few days of a month.
		const thisMonth = await listScheduledMeetings(token, now.getFullYear(), now.getMonth() + 1);
		const nextMonthDate = new Date(now.getFullYear(), now.getMonth() + 1, 1);
		const nextMonth = await listScheduledMeetings(
			token,
			nextMonthDate.getFullYear(),
			nextMonthDate.getMonth() + 1
		);
		meetings = [...thisMonth.meetings, ...nextMonth.meetings];
	} catch (error) {
		meetingsError = error instanceof ApiError ? error.message : 'Could not load meetings.';
	}

	const today = todayIso();
	const upcoming = meetings
		.filter((m) => m.status === 'scheduled' && m.date >= today)
		.sort((a, b) => (a.date + a.start_time).localeCompare(b.date + b.start_time));

	return {
		todayMeetings: upcoming.filter((m) => m.date === today),
		laterMeetings: upcoming.filter((m) => m.date !== today).slice(0, 5),
		meetingsError
	};
};
