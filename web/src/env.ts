import { defineEnvVars } from '@sveltejs/kit/env';

// WAITLIST_* are optional at the type/build level — the CTA form action checks for
// their presence at request time and fails gracefully if they're unset, so
// the site still builds and runs cleanly from a freshly cloned .env.example.
//
// BACKEND_URL and SESSION_COOKIE_SECURE are server-only: every call to the FastAPI
// backend is made from SvelteKit server code (load functions, actions, +server.ts
// routes) — never from the browser — so the session token never has to leave the
// server as anything other than an httpOnly cookie. See src/lib/server/api.ts.
export const variables = defineEnvVars({
	WAITLIST_URL: {
		schema: (value: string | undefined) => value || undefined,
		description: 'Google Apps Script web app URL that receives early-access signups.'
	},
	WAITLIST_SECRET: {
		schema: (value: string | undefined) => value || undefined,
		description: 'Shared secret sent with every signup request to the waitlist webhook.'
	},
	BACKEND_URL: {
		schema: (value: string | undefined) => value || 'http://localhost:8000',
		description: 'Base URL of the SynkAI FastAPI backend, called only from server-side code.'
	},
	SESSION_COOKIE_SECURE: {
		schema: (value: string | undefined) => value !== 'false',
		description:
			'Whether the session cookie requires HTTPS. Defaults to true; set to "false" only for ' +
			'plain-HTTP local development.'
	}
});
