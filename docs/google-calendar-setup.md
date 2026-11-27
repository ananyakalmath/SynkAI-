# Google Calendar setup

SynkAI can create a Google Calendar event — with a Google Meet link — when a
meeting's organiser has connected their Google account under **Profile → Google
Calendar**. This is optional per-user: anyone who doesn't connect it still gets the
existing emailed invite (an `.ics` attachment via SMTP).

This reuses the same OAuth client used for "Sign in with Google" (Phase 1). If you
already have `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` configured and sign-in works,
you only need to do step 3 (enable the Calendar API) and step 5 (generate an
encryption key) below.

## 1. Enable the Google Calendar API

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and select (or
   create) the project you use for SynkAI's sign-in.
2. Go to **APIs & Services → Library**, search for **Google Calendar API**, and click
   **Enable**.

## 2. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**.
2. If you haven't already, set **User type** to **External** and keep **Publishing
   status** as **Testing** (this app is not going through Google's verification
   review — testing mode is fine for internal/personal use).
3. Under **Test users**, add the Google account(s) of anyone who will click "Connect
   Google Calendar". Only test users can complete this flow while the app is
   unverified.
4. Add the scope `.../auth/calendar.events` under **Scopes** if prompted — SynkAI
   requests it incrementally (only when a user clicks "Connect"), not at sign-in.

## 3. Create (or reuse) an OAuth client

1. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Web application**.
3. Under **Authorized redirect URIs**, add the same URL you use for sign-in — by
   default `http://localhost:8501` (the Streamlit app's own URL; it's where Google
   redirects back with the authorization code for both sign-in and calendar
   connection).
4. Save, and copy the **Client ID** and **Client Secret**.

## 4. Set the environment variables

In `.env` (not `.env.example` — that one stays blank and is committed):

```
GOOGLE_CLIENT_ID=<your client id>
GOOGLE_CLIENT_SECRET=<your client secret>
GOOGLE_REDIRECT_URI=http://localhost:8501
```

## 5. Generate a token encryption key

Google Calendar refresh tokens are long-lived credentials, so SynkAI encrypts them
before storing them. Generate a key once:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the result in `.env`:

```
TOKEN_ENCRYPTION_KEY=<the generated key>
```

Changing this key later makes any already-stored connections undecryptable — anyone
connected will need to click "Connect Google Calendar" again.

## How it behaves

- **Connected organiser**: on create/update, SynkAI creates/updates a Google Calendar
  event on the organiser's own calendar, with a Meet link, and asks Google to email
  every attendee (`sendUpdates=all`) — SynkAI does not also send its own SMTP invite
  in this case. On cancel, SynkAI deletes the Google event (Google emails the
  cancellation). The event ID and Meet link are saved on the meeting and shown in the
  Streamlit calendar view.
- **Not connected, or the Google API call fails**: SynkAI falls back to emailing every
  participant directly via SMTP with a standard `.ics` attachment — the same behaviour
  as before this integration existed. A failure is recorded as the meeting's
  `calendar_sync_error` and shown in the UI; SynkAI never claims a Meet link exists
  when it doesn't.
