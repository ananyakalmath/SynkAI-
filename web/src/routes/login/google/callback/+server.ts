import { redirect } from '@sveltejs/kit';
import { ApiError, googleCallback } from '#lib/server/api.js';
import { setSessionCookie } from '#lib/server/session.js';
import { postLoginRedirect } from '#lib/server/auth-redirect.js';
import type { RequestHandler } from './$types';

// Google redirects here with ?code=&state= after the user approves (or denies)
// access. This exchanges the code for a session server-side and sets the httpOnly
// cookie — the browser never sees the bearer token itself.
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
