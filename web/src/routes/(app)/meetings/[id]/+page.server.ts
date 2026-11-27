import { error, fail, redirect } from '@sveltejs/kit';
import {
	ApiError,
	cancelScheduledMeeting,
	getScheduledMeeting,
	updateScheduledMeeting
} from '#lib/server/api.js';
import { parseMeetingForm } from '#lib/server/meeting-form.js';
import { getSessionToken } from '#lib/server/session.js';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, params }) => {
	const token = getSessionToken(cookies) as string; // guaranteed by (app)/+layout.server.ts

	try {
		const meeting = await getScheduledMeeting(token, params.id);
		return { meeting };
	} catch (err) {
		if (err instanceof ApiError && err.status === 404) {
			throw error(404, 'Meeting not found.');
		}
		throw err;
	}
};

export const actions: Actions = {
	update: async ({ request, cookies, params }) => {
		const token = getSessionToken(cookies) as string;
		const form = await request.formData();
		const parsed = parseMeetingForm(form);
		if ('message' in parsed) {
			return fail(400, { error: parsed.message });
		}

		try {
			const result = await updateScheduledMeeting(token, params.id, parsed);
			return { updated: result };
		} catch (err) {
			const message = err instanceof ApiError ? err.message : 'Could not update the meeting.';
			return fail(err instanceof ApiError ? err.status : 502, { error: message });
		}
	},

	cancel: async ({ cookies, params }) => {
		const token = getSessionToken(cookies) as string;

		try {
			await cancelScheduledMeeting(token, params.id);
		} catch (err) {
			const message = err instanceof ApiError ? err.message : 'Could not cancel the meeting.';
			return fail(err instanceof ApiError ? err.status : 502, { error: message });
		}

		throw redirect(303, '/calendar');
	}
};
