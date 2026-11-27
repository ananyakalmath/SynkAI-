import { redirect } from '@sveltejs/kit';
import { ApiError, googleLoginUrl } from '#lib/server/api.js';
import type { RequestHandler } from './$types';

// Kicks off Google sign-in: asks the backend for a CSRF-guarded consent-screen URL
// (optionally carrying an invite code through the round trip) and redirects the
// browser there directly. No client-side JS ever sees a client secret or builds
// this URL itself.
export const GET: RequestHandler = async ({ url }) => {
	const inviteCode = url.searchParams.get('invite') ?? undefined;

	try {
		const { authorization_url } = await googleLoginUrl(inviteCode);
		throw redirect(302, authorization_url, { external: true });
	} catch (error) {
		if (error instanceof ApiError) {
			throw redirect(303, `/login?error=${encodeURIComponent(error.message)}`);
		}
		throw error;
	}
};
