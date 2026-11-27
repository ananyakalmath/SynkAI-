import { redirect } from '@sveltejs/kit';
import { ApiError, googleCalendarConnectUrl } from '#lib/server/api.js';
import { getSessionToken } from '#lib/server/session.js';
import type { RequestHandler } from './$types';

// Kicks off the "Connect Google Calendar" incremental-authorization redirect for the
// signed-in user. The completion lands at /login/google/callback (the one registered
// redirect URI), which branches back to /calendar based on the state's "cal_" prefix.
export const GET: RequestHandler = async ({ cookies }) => {
	const token = getSessionToken(cookies);
	if (!token) throw redirect(303, '/login');

	try {
		const { authorization_url } = await googleCalendarConnectUrl(token);
		throw redirect(302, authorization_url, { external: true });
	} catch (error) {
		if (error instanceof ApiError) {
			throw redirect(303, `/calendar?calendar_error=${encodeURIComponent(error.message)}`);
		}
		throw error;
	}
};
