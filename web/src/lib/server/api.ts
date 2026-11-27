// Server-only client for the SynkAI FastAPI backend. Every function here runs in
// SvelteKit server code (load functions, form actions, +server.ts routes) — never in
// the browser — so the bearer session token only ever exists server-side, bridged to
// the browser as an httpOnly cookie (see session.ts), never localStorage.

import { BACKEND_URL } from '$app/env/private';

export class ApiError extends Error {
	status: number;

	constructor(message: string, status: number) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
	}
}

const DEFAULT_TIMEOUT_MS = 15_000;

type DetailPayload = { detail?: unknown };

function hasDetailField(payload: unknown): payload is DetailPayload {
	return typeof payload === 'object' && payload !== null && 'detail' in payload;
}

function stringifyDetailItem(item: unknown): string {
	if (item && typeof item === 'object') {
		if ('msg' in item) return String(item.msg);
		return JSON.stringify(item);
	}
	return String(item);
}

function extractDetail(payload: unknown): string {
	if (!hasDetailField(payload)) {
		return typeof payload === 'string' ? payload : JSON.stringify(payload);
	}

	const detail: unknown = payload.detail;
	if (Array.isArray(detail) && detail.length > 0) {
		return stringifyDetailItem((detail as unknown[])[0]);
	}
	return stringifyDetailItem(detail);
}

type ApiFetchOptions = {
	method?: string;
	token?: string;
	json?: unknown;
	params?: Record<string, string | number | undefined>;
	timeoutMs?: number;
};

async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
	const { method = 'GET', token, json, params, timeoutMs = DEFAULT_TIMEOUT_MS } = options;

	const url = new URL(path, BACKEND_URL);
	if (params) {
		for (const [key, value] of Object.entries(params)) {
			if (value !== undefined) url.searchParams.set(key, String(value));
		}
	}

	const headers: Record<string, string> = {};
	if (token) headers['Authorization'] = `Bearer ${token}`;
	if (json !== undefined) headers['Content-Type'] = 'application/json';

	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), timeoutMs);

	let response: Response;
	try {
		response = await fetch(url, {
			method,
			headers,
			body: json !== undefined ? JSON.stringify(json) : undefined,
			signal: controller.signal
		});
	} catch (error) {
		if (error instanceof Error && error.name === 'AbortError') {
			throw new ApiError(`The request to ${path} timed out after ${timeoutMs}ms.`, 504);
		}
		throw new ApiError(`Could not reach the SynkAI backend at ${BACKEND_URL}. Is it running?`, 503);
	} finally {
		clearTimeout(timer);
	}

	const text = await response.text();
	const payload: unknown = text ? JSON.parse(text) : null;

	if (!response.ok) {
		throw new ApiError(extractDetail(payload), response.status);
	}

	return payload as T;
}

// ----------------------------------------------------------------------------
// Types (mirroring backend/models/*.py — only the fields the web app reads)
// ----------------------------------------------------------------------------

export type WorkspaceInfo = {
	id: string;
	company_name: string;
	domain: string | null;
};

export type UserProfile = {
	id: string;
	email: string;
	full_name: string | null;
	onboarded: boolean;
	google_connected: boolean;
	role_title: string | null;
	workspace: WorkspaceInfo | null;
	membership_role: 'admin' | 'member' | null;
	membership_status: 'active' | 'pending' | null;
};

export type AuthResult = {
	session_token: string;
	user: UserProfile;
	invite_code: string | null;
};

export type GoogleLoginUrlResponse = {
	authorization_url: string;
	state: string;
};

export type Participant = { name: string; email: string };

export type ScheduledMeeting = {
	id: string;
	workspace_id: string;
	organiser: { user_id: string; name: string | null; email: string };
	title: string;
	objective: string | null;
	meeting_type: string;
	date: string;
	start_time: string;
	end_time: string;
	timezone: string;
	location: string | null;
	status: 'scheduled' | 'cancelled';
	participants: Participant[];
	document_ids: string[];
	previous_document_id: string | null;
	sequence: number;
	reminder_24h_enabled: boolean;
	reminder_1h_enabled: boolean;
	google_event_id: string | null;
	google_meet_link: string | null;
	calendar_sync_error: string | null;
	created_at: string;
	updated_at: string;
};

// ----------------------------------------------------------------------------
// Auth
// ----------------------------------------------------------------------------

export function googleLoginUrl(inviteCode?: string): Promise<GoogleLoginUrlResponse> {
	return apiFetch('/auth/google/login', { params: { invite_code: inviteCode } });
}

export function googleCallback(code: string, state: string): Promise<AuthResult> {
	return apiFetch('/auth/google/callback', { method: 'POST', json: { code, state } });
}

export function requestEmailCode(email: string): Promise<{ message: string }> {
	return apiFetch('/auth/email/request-code', { method: 'POST', json: { email } });
}

export function verifyEmailCode(email: string, code: string): Promise<AuthResult> {
	return apiFetch('/auth/email/verify-code', { method: 'POST', json: { email, code } });
}

export function getMe(token: string): Promise<UserProfile> {
	return apiFetch('/auth/me', { token });
}

export function submitOnboarding(
	token: string,
	data: { full_name: string; role_title: string; company_name?: string; invite_code?: string }
): Promise<UserProfile> {
	return apiFetch('/auth/onboarding', { method: 'POST', token, json: data });
}

export function logout(token: string): Promise<{ message: string }> {
	return apiFetch('/auth/logout', { method: 'POST', token });
}

export function logoutAll(token: string): Promise<{ message: string }> {
	return apiFetch('/auth/logout-all', { method: 'POST', token });
}

// ----------------------------------------------------------------------------
// Scheduled meetings (dashboard, calendar)
// ----------------------------------------------------------------------------

export function listScheduledMeetings(
	token: string,
	year: number,
	month: number
): Promise<{ meetings: ScheduledMeeting[] }> {
	return apiFetch('/scheduled-meetings', { token, params: { year, month } });
}
