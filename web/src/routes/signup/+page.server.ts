import { redirectAwayIfSignedIn } from '#lib/server/auth-redirect.js';
import type { PageServerLoad } from './$types';

// /signup has no backend endpoints of its own — Google sign-in and the emailed
// one-time code both create an account automatically on first use. This route
// reuses /login's form actions (see LoginForm's `actionBase` prop) and only
// differs in headline copy, matching the backend's actual auth model instead of
// inventing a separate "create account" flow it doesn't have.
export const load: PageServerLoad = async ({ cookies, url }) => {
	await redirectAwayIfSignedIn(cookies, url.searchParams.get('invite'));

	return {
		inviteCode: url.searchParams.get('invite'),
		oauthError: url.searchParams.get('error')
	};
};
