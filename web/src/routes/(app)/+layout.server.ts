import { redirect } from '@sveltejs/kit';
import { ApiError, getMe } from '#lib/server/api.js';
import { clearSessionCookie, getSessionToken } from '#lib/server/session.js';
import type { LayoutServerLoad } from './$types';

// The single gate every authenticated app page sits behind: no session → /login,
// not onboarded or membership pending → /onboarding. Every (app) page's own load
// function can assume `data.user` is a fully onboarded, active member.
export const load: LayoutServerLoad = async ({ cookies }) => {
	const token = getSessionToken(cookies);
	if (!token) throw redirect(303, '/login');

	let user;
	try {
		user = await getMe(token);
	} catch (error) {
		if (error instanceof ApiError) {
			clearSessionCookie(cookies);
			throw redirect(303, '/login');
		}
		throw error;
	}

	if (!user.onboarded || user.membership_status === 'pending') {
		throw redirect(303, '/onboarding');
	}

	return { user };
};
