// single source of truth for every fact used on the page.
// nothing here is invented: no customers, stats, testimonials or logos.

export const product = {
	name: 'SynkAI',
	tagline: 'The AI Boardroom Copilot',
	status:
		'In active development — the screens below are illustrative previews, not live product captures.'
};

export const lifecycle = [
	{
		id: 'before',
		step: '01',
		label: 'Before',
		title: 'The room is ready before anyone sits down',
		body: 'SynkAI creates the meeting, auto-generates an agenda and an intelligent pre-meeting brief, and pulls in the organisational knowledge and previous decisions that matter to this conversation.'
	},
	{
		id: 'during',
		step: '02',
		label: 'During',
		title: 'Nothing said in the room is lost',
		body: 'Live transcription and live AI insight run as the meeting happens. Ask Synk anything about the current or a past meeting. Decisions, risks and unanswered questions are captured as they occur.'
	},
	{
		id: 'after',
		step: '03',
		label: 'After',
		title: 'The record writes itself',
		body: 'Structured minutes, action items, decisions, deadlines, risks and open questions — each linked to the person responsible for it.'
	},
	{
		id: 'follow-through',
		step: '04',
		label: 'Follow-through',
		title: 'Action items do not go quiet',
		body: 'Every action item becomes a tracked task with an owner, a deadline, a status, reminders and overdue tracking.'
	},
	{
		id: 'next-meeting',
		step: '05',
		label: 'Next meeting',
		title: 'The loop closes itself',
		body: 'Previous decisions, unresolved tasks and outstanding risks feed directly into the next agenda and brief — a continuous intelligence loop, not a one-off summary.'
	}
] as const;

export const beforeDemo = {
	agenda: [
		'Review Q3 rollout readiness',
		'Vendor contract status',
		'Open risks carried from last meeting'
	],
	brief:
		'Three items carry forward from the last sync: the rollout date, the vendor countersignature, and on-call coverage. Relevant decisions and documents are already attached below.'
};

export const duringTranscript = [
	{
		t: '00:04:12',
		speaker: 'R. Alam',
		text: "Let's lock the Q3 rollout date before we move on.",
		tag: null
	},
	{
		t: '00:04:26',
		speaker: 'J. Costa',
		text: 'Agreed — I can commit engineering to the 18th.',
		tag: 'decision'
	},
	{
		t: '00:05:03',
		speaker: 'R. Alam',
		text: 'Vendor contract still has not been countersigned.',
		tag: 'risk'
	},
	{
		t: '00:05:41',
		speaker: 'P. Nair',
		text: 'Who owns chasing legal on that this week?',
		tag: 'question'
	}
] as const;

export const askSynk = {
	question: 'Ask Synk — what did we decide about the Q3 rollout date?',
	answer:
		'On 14 Nov, the team committed to an 18 Nov rollout. One open risk: the vendor contract is still awaiting countersignature.'
};

export const minutes = {
	decisions: ['Q3 rollout date locked for 18 Nov.'],
	actionItems: [
		{ owner: 'J. Costa', task: 'Prepare engineering handoff for rollout', due: '16 Nov' },
		{ owner: 'P. Nair', task: 'Chase legal on vendor countersignature', due: '13 Nov' }
	],
	openQuestions: ['Who covers on-call during the rollout window?']
};

export const tasks = [
	{ owner: 'J. Costa', task: 'Prepare engineering handoff', due: '16 Nov', status: 'on-track' },
	{ owner: 'P. Nair', task: 'Chase legal on countersignature', due: '13 Nov', status: 'overdue' },
	{ owner: 'R. Alam', task: 'Confirm on-call coverage', due: '15 Nov', status: 'done' }
] as const;

export const nextMeeting = {
	line: 'The next meeting begins where the last one ended.'
};

export const underTheHood = {
	intro: 'SynkAI is built to run close to your own data, not to send it away.',
	points: [
		{
			title: 'Local-first by design',
			body: 'The language model runs on your own infrastructure via Ollama (qwen3) — your meetings do not need to leave your environment to be understood.'
		},
		{
			title: 'Retrieval over your own knowledge',
			body: 'A RAG layer on ChromaDB retrieves relevant organisational knowledge and prior decisions, so every brief and insight is grounded in what your organisation actually agreed.'
		},
		{
			title: 'A multi-agent pipeline, not one monolithic prompt',
			body: 'A LangGraph workflow coordinates specialised agents — parser, summary, action-item, decision, deadline and risk agents — overseen by a coordinator agent that reconciles their output into one consistent record.'
		}
	]
};

export const agentPipeline = [
	{ id: 'parser', name: 'Parser agent', role: 'Structures the raw transcript' },
	{ id: 'summary', name: 'Summary agent', role: 'Condenses discussion into a narrative' },
	{ id: 'action', name: 'Action-item agent', role: 'Extracts tasks and owners' },
	{ id: 'decision', name: 'Decision agent', role: 'Flags agreed decisions' },
	{ id: 'deadline', name: 'Deadline agent', role: 'Attaches dates and timelines' },
	{ id: 'risk', name: 'Risk agent', role: 'Surfaces risks and open questions' },
	{ id: 'coordinator', name: 'Coordinator agent', role: 'Reconciles every agent into one record' }
] as const;

export const doors = {
	headline: 'Every decision starts in the room.'
};

export const walkIn = {
	headline: 'SynkAI. The AI Boardroom Copilot.'
};

export const cta = {
	heading: 'Request early access',
	body: 'SynkAI is in development. Leave your details and we will be in touch as early access opens.',
	submitLabel: 'Request access',
	successMessage: "You're on the list — we'll be in touch as early access opens.",
	errorMessage: 'Something went wrong on our end. Please try again in a moment.'
};

export const footer = {
	wordmark: 'SynkAI',
	note: 'SynkAI is in active development. [YOUR TEXT — legal / company address / registration details]',
	links: [
		{ label: 'Privacy', href: '#' },
		{ label: 'Contact', href: '#' }
	]
};
