import { fail, redirect } from '@sveltejs/kit';
import { ApiError, getMe, submitOnboarding } from '#lib/server/api.js';
import { clearSessionCookie, getSessionToken } from '#lib/server/session.js';
import { postLoginRedirect } from '#lib/server/auth-redirect.js';
import type { Actions, PageServerLoad } from './$types';

function asString(value: FormDataEntryValue | null): string {
	return typeof value === 'string' ? value.trim() : '';
}

export const load: PageServerLoad = async ({ cookies, url }) => {
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

	if (user.onboarded && user.membership_status === 'active') {
		throw redirect(303, '/dashboard');
	}

	return {
		user,
		pending: user.onboarded && user.membership_status === 'pending',
		inviteCode: url.searchParams.get('invite')
	};
};

export const actions: Actions = {
	submit: async ({ request, cookies }) => {
		const token = getSessionToken(cookies);
		if (!token) throw redirect(303, '/login');

		const form = await request.formData();
		const fullName = asString(form.get('full_name'));
		const roleTitle = asString(form.get('role_title'));
		const companyName = asString(form.get('company_name'));
		const inviteCode = asString(form.get('invite_code')) || undefined;

		if (!fullName || !roleTitle) {
			return fail(400, { error: 'Please fill in your name and role.' });
		}
		if (!inviteCode && !companyName) {
			return fail(400, { error: 'Please enter your company name.' });
		}

		let user;
		try {
			user = await submitOnboarding(token, {
				full_name: fullName,
				role_title: roleTitle,
				company_name: companyName || undefined,
				invite_code: inviteCode
			});
		} catch (error) {
			const message = error instanceof ApiError ? error.message : 'Could not complete onboarding.';
			return fail(error instanceof ApiError ? error.status : 502, { error: message });
		}

		throw redirect(303, postLoginRedirect(user, null));
	},

	checkAgain: async ({ cookies }) => {
		const token = getSessionToken(cookies);
		if (!token) throw redirect(303, '/login');

		const user = await getMe(token);
		if (user.membership_status === 'active') {
			throw redirect(303, '/dashboard');
		}
		return { pending: true };
	}
};
