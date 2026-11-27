import { fail, redirect } from '@sveltejs/kit';
import { ApiError, requestEmailCode, verifyEmailCode } from '#lib/server/api.js';
import { setSessionCookie } from '#lib/server/session.js';
import { postLoginRedirect, redirectAwayIfSignedIn } from '#lib/server/auth-redirect.js';
import type { Actions, PageServerLoad } from './$types';

function asString(value: FormDataEntryValue | null): string {
	return typeof value === 'string' ? value.trim() : '';
}

export const load: PageServerLoad = async ({ cookies, url }) => {
	await redirectAwayIfSignedIn(cookies, url.searchParams.get('invite'));

	return {
		inviteCode: url.searchParams.get('invite'),
		oauthError: url.searchParams.get('error')
	};
};

export const actions: Actions = {
	requestCode: async ({ request }) => {
		const form = await request.formData();
		const email = asString(form.get('email'));
		const inviteCode = asString(form.get('invite_code')) || undefined;

		if (!email) {
			return fail(400, {
				stage: 'request',
				email,
				inviteCode,
				error: 'Please enter your work email.'
			});
		}

		try {
			await requestEmailCode(email);
		} catch (error) {
			const message = error instanceof ApiError ? error.message : 'Could not send a sign-in code.';
			return fail(error instanceof ApiError ? error.status : 502, {
				stage: 'request',
				email,
				inviteCode,
				error: message
			});
		}

		return { stage: 'verify', email, inviteCode };
	},

	verifyCode: async ({ request, cookies }) => {
		const form = await request.formData();
		const email = asString(form.get('email'));
		const code = asString(form.get('code'));
		const inviteCode = asString(form.get('invite_code')) || undefined;

		if (!code) {
			return fail(400, { stage: 'verify', email, inviteCode, error: 'Please enter the code.' });
		}

		let result;
		try {
			result = await verifyEmailCode(email, code);
		} catch (error) {
			const message = error instanceof ApiError ? error.message : 'Could not verify that code.';
			return fail(error instanceof ApiError ? error.status : 502, {
				stage: 'verify',
				email,
				inviteCode,
				error: message
			});
		}

		setSessionCookie(cookies, result.session_token);
		throw redirect(303, postLoginRedirect(result.user, inviteCode ?? null));
	},

	restart: () => {
		return { stage: 'request' };
	}
};
