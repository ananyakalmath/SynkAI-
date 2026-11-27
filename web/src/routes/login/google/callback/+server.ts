import { redirect } from '@sveltejs/kit';
import { ApiError, googleCallback, googleCalendarCallback } from '#lib/server/api.js';
import { setSessionCookie } from '#lib/server/session.js';
import { postLoginRedirect } from '#lib/server/auth-redirect.js';
import type { RequestHandler } from './$types';

// Google only redirects to one registered URI, so both ordinary sign-in and the
// "Connect Google Calendar" incremental-authorization flow (Phase B) land here with
// the same ?code=&state= shape. The `state` value itself says which one — a
// calendar-connect state is prefixed "cal_" by the backend (see
// auth_service.create_calendar_connect_state) — so no extra round trip is needed
// just to ask which flow a redirect belongs to.
export const GET: RequestHandler = async ({ url, cookies }) => {
	const code = url.searchParams.get('code');
	const state = url.searchParams.get('state');

	if (!code || !state) {
		const deniedReason = url.searchParams.get('error');
		const message =
			deniedReason === 'access_denied'
				? 'Google sign-in was cancelled.'
				: 'Google did not return the expected sign-in details.';
		throw redirect(303, `/login?error=${encodeURIComponent(message)}`);
	}

	if (state.startsWith('cal_')) {
		try {
			await googleCalendarCallback(code, state);
		} catch (error) {
			const message =
				error instanceof ApiError ? error.message : 'Could not connect Google Calendar.';
			throw redirect(303, `/calendar?calendar_error=${encodeURIComponent(message)}`);
		}
		throw redirect(303, '/calendar?calendar_connected=1');
	}

	let result;
	try {
		result = await googleCallback(code, state);
	} catch (error) {
		const message =
			error instanceof ApiError ? error.message : 'Google sign-in failed unexpectedly.';
		throw redirect(303, `/login?error=${encodeURIComponent(message)}`);
	}

	setSessionCookie(cookies, result.session_token);
	throw redirect(303, postLoginRedirect(result.user, result.invite_code));
};
