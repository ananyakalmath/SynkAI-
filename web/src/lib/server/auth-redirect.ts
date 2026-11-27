import { redirect, type Cookies } from '@sveltejs/kit';
import { ApiError, getMe, type UserProfile } from './api.js';
import { clearSessionCookie, getSessionToken } from './session.js';

/**
 * Where to send a user right after a session is established — shared by the
 * email-code flow, the Google callback, and the onboarding form itself.
 */
export function postLoginRedirect(user: UserProfile, inviteCode: string | null): string {
	if (!user.onboarded || user.membership_status === 'pending') {
		return inviteCode ? `/onboarding?invite=${encodeURIComponent(inviteCode)}` : '/onboarding';
	}
	return '/dashboard';
}

/**
 * Used by /login and /signup's `load`: if a valid session cookie already exists,
 * skip the sign-in form entirely and go straight to wherever that session belongs.
 * A stale/expired cookie is cleared rather than looping the user back here.
 */
export async function redirectAwayIfSignedIn(
	cookies: Cookies,
	inviteCode: string | null
): Promise<void> {
	const token = getSessionToken(cookies);
	if (!token) return;

	let user: UserProfile;
	try {
		user = await getMe(token);
	} catch (error) {
		if (error instanceof ApiError) {
			clearSessionCookie(cookies);
			return;
		}
		throw error;
	}

	throw redirect(303, postLoginRedirect(user, inviteCode));
}
