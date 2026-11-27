// The SynkAI session token never reaches the browser as anything but an httpOnly
// cookie — it is never stored in localStorage or read by client-side JS. The token
// itself is still the same opaque bearer token the FastAPI backend issues; this
// module only decides how it travels between this SvelteKit server and the browser.

import type { Cookies } from '@sveltejs/kit';
import { SESSION_COOKIE_SECURE } from '$app/env/private';

export const SESSION_COOKIE = 'synkai_session';

const THIRTY_DAYS = 60 * 60 * 24 * 30;

export function setSessionCookie(cookies: Cookies, token: string): void {
	cookies.set(SESSION_COOKIE, token, {
		path: '/',
		httpOnly: true,
		secure: SESSION_COOKIE_SECURE,
		sameSite: 'lax',
		maxAge: THIRTY_DAYS
	});
}

export function clearSessionCookie(cookies: Cookies): void {
	cookies.delete(SESSION_COOKIE, { path: '/' });
}

export function getSessionToken(cookies: Cookies): string | undefined {
	return cookies.get(SESSION_COOKIE);
}
