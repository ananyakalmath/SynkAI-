import { fail } from '@sveltejs/kit';
import { WAITLIST_URL, WAITLIST_SECRET } from '$app/env/private';
import type { Actions } from './$types';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function asString(value: FormDataEntryValue | null): string {
	return typeof value === 'string' ? value.trim() : '';
}

export const actions: Actions = {
	default: async ({ request }) => {
		const form = await request.formData();
		const email = asString(form.get('email'));
		const company = asString(form.get('company'));
		// honeypot: real visitors never fill this in, bots filling every field do
		const honeypot = asString(form.get('website'));

		if (honeypot) {
			// silently pretend to succeed so the bot moves on
			return { success: true };
		}

		if (!email || !EMAIL_PATTERN.test(email)) {
			return fail(400, {
				success: false,
				error: 'Please enter a valid work email address.',
				email,
				company
			});
		}

		if (!WAITLIST_URL || !WAITLIST_SECRET) {
			console.error('WAITLIST_URL or WAITLIST_SECRET is not configured.');
			return fail(500, {
				success: false,
				error: 'Something went wrong on our end. Please try again in a moment.',
				email,
				company
			});
		}

		try {
			const response = await fetch(WAITLIST_URL, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					secret: WAITLIST_SECRET,
					email,
					company,
					submittedAt: new Date().toISOString()
				})
			});

			if (!response.ok) {
				console.error('Waitlist webhook responded with', response.status);
				return fail(502, {
					success: false,
					error: 'Something went wrong on our end. Please try again in a moment.',
					email,
					company
				});
			}
		} catch (error) {
			console.error('Waitlist webhook request failed', error);
			return fail(502, {
				success: false,
				error: 'Something went wrong on our end. Please try again in a moment.',
				email,
				company
			});
		}

		return { success: true };
	}
};
