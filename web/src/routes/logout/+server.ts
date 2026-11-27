import { redirect } from '@sveltejs/kit';
import { logout } from '#lib/server/api.js';
import { clearSessionCookie, getSessionToken } from '#lib/server/session.js';
import type { RequestHandler } from './$types';

// A plain POST endpoint (not a page) so any form in the app — the pending-approval
// screen, the app shell's sidebar — can sign out with `<form method="POST" action="/logout">`
// without duplicating this logic per route.
export const POST: RequestHandler = async ({ cookies }) => {
	const token = getSessionToken(cookies);
	if (token) {
		try {
			await logout(token);
		} catch {
			// Even if the backend call fails, still clear the local cookie below —
			// never leave the browser holding a cookie it believes is a live session.
		}
	}

	clearSessionCookie(cookies);
	throw redirect(303, '/login');
};
