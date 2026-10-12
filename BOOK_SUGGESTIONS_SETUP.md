# Book suggestions: Formspree connection and email verification

## Current status

The existing form is now enabled and connected to the owner-provided public endpoint **https://formspree.io/f/xwlvnbrl**. It submits JSON by HTTPS POST without opening an email app or requiring visitor accounts/email addresses. Notifications to **jon3107bok@gmail.com** are controlled by the Formspree account, not selected by public JavaScript. Recipient verification and notifications must be checked there.

**Live mailbox delivery has not been tested.** No real submissions or test emails were sent during this activation task. A recognised HTTP-success acceptance response produces “Tillagan þín hefur verið send!”; this confirms Formspree acceptance, not that Gmail has received the notification. Verify the recipient and email notification action, then perform the single deployed-site test below.

Formspree was selected because its form-ID endpoints support GitHub Pages, JSON AJAX submissions, configurable email notifications, honeypots, domain restrictions and provider rate limits without visitor accounts or email addresses. This integration uses native `fetch`, not an added library. A form ID is public configuration; it is not an API secret.

## Verify the existing form and notifications

1. Sign in to the Formspree account that owns form **xwlvnbrl**. The form already exists; do not create another one. Confirm `jon3107bok@gmail.com` is added as the notification recipient and complete any pending recipient/account verification email. Visitors do not register.
2. In the form's email notification action, confirm that notifications are enabled and delivered to that recipient. Use the submitted `subject` field for the email subject, rather than overriding it with a fixed dashboard subject. The form supplies `Bókasafn — Ný bókatillaga: [title]`. Keep the standard notification fields and `message` visible; all supplied optional details appear in the readable message too.
3. Add server-side field validation in the dashboard/claim form where available: `Bókatitill` required/max 140, `Höfundur` required/max 120, `Bókaflokkur` optional/max 140, `Ástæða fyrir tillögu` optional/max 2000, `Hlekkur á Forlagið` optional/max 600. Do **not** require an `email` field. Frontend limits improve usability; they are not a substitute for provider protections against direct requests.
4. In **Project → Settings → Restrict to Domain**, enter the actual deployed hostname, normally `b10xdragon.github.io`, without `https://` or `/bokasafn`. If GitHub Pages uses a custom domain, use that hostname instead. Confirm the hostname from the actual Pages deployment. Localhost submissions will not be accepted after this restriction is enabled; use the deployed site for the real test. The request sends an origin referrer as required by Formspree's documented domain check.
5. Keep Formspree's automatic spam filtering and the form's `_gotcha` honeypot. Formspree documents a **20 posts/minute/form** system rate limit and plan-based monthly quotas; choose a plan appropriate to expected use and monitor submissions/spam. Domain restrictions are an additional spam signal, not authentication. The fixed recipient is configured at the provider; the frontend cannot choose arbitrary recipients.
6. Under **Form → Settings → Spam protection**, ensure the ordinary JSON AJAX endpoint works without an interactive CAPTCHA redirect. This implementation does not render a CAPTCHA widget. If reCAPTCHA is enabled, disable that interactive challenge for this form, keeping the other protections above. Alternatively temporarily set `enabled: false` until a separately configured on-page CAPTCHA integration is added. Never put a CAPTCHA secret or Gmail password in the repository. See the provider's [reCAPTCHA settings](https://help.formspree.io/articles/form-and-project-settings/recaptcha-settings/).
7. Endpoint activation is already committed in `js/suggestion-config.js`:

   ```js
   globalThis.BOKASAFN_SUGGESTIONS = {
       enabled: true,
       endpoint: 'https://formspree.io/f/xwlvnbrl'
   };
   ```

   Only the public form ID is embedded. No private API key, password or SMTP credential is needed. The script cache versions have been updated. Confirm which branch GitHub Pages publishes: this task pushes **Beta only**, and does not modify or merge into main. A Pages deployment must include the Beta changes before visitors can use this version.
8. From the deployed site, submit one clearly labelled test suggestion such as **Prófun — Bókasafn** with a real author and optional series/reason/Forlagið product link. Confirm the browser reports acceptance, the submission appears in Formspree's inbox, and the email actually reaches `jon3107bok@gmail.com` with the exact subject and all provided details. Check Gmail spam too. Provider acceptance alone does not prove final mailbox delivery.
9. If the real test fails, set `enabled: false`, publish that configuration and resolve recipient verification, notification settings, CAPTCHA, quota or domain restrictions. Do not label email delivery operational until step 8 succeeds. Never load-test the public provider endpoint.
10. Review/delete old submissions periodically in the provider dashboard according to school privacy requirements. The site does not collect visitor email addresses or persist suggestion drafts in browser storage. Formspree processes submission text and normal request metadata; its own privacy policy applies. Visitors are asked not to include personal information.

## Verified documentation and test limits

Provider documentation inspected on 2026-10-12:

- [Static integration and claim URL syntax](https://formspree.io/llms.txt)
- [AJAX submissions](https://help.formspree.io/articles/building-your-form/submit-forms-with-javascript-ajax/)
- [Email subject field](https://help.formspree.io/articles/building-your-form/email-subject-line/): `subject`, available on all plans.
- [Honeypot](https://help.formspree.io/articles/building-your-form/honeypot-spam-filtering/): `_gotcha`.
- [Domain restrictions](https://help.formspree.io/articles/form-and-project-settings/restrict-to-domain/)
- [Spam protection](https://help.formspree.io/articles/troubleshooting/how-to-prevent-spam/)
- [System and AJAX rate limits](https://help.formspree.io/articles/form-and-project-settings/system-limits/)
- The published [Formspree AJAX client](https://unpkg.com/@formspree/ajax@1), using core v4, recognises a JSON `next` string as success and an `error`/`errors` field as failure. Our native integration additionally requires an HTTP success status, accepts the explicit `ok: true` success marker used by other Formspree response versions, rejects error/unrecognised bodies, and never follows the returned URL.

Automated tests intercept the configured form-ID URL and simulate this documented response format, network failure, 500, 429 and unexpected bodies. These tests exercise the browser integration without transmitting visitor data or emails. **They are not an end-to-end provider/mailbox test.** The real end-to-end test in step 8 remains pending; the endpoint itself is already configured. Mocked Chromium, Firefox and Linux WebKit runs send no live emails. Linux WebKit is not physical Safari/iOS testing.

Activation verification: **145 distinct unit cases**, **275 executions** including three time zones, and **108 browser groups passed**. The actual configured endpoint was intercepted in all suggestion tests; **zero real test emails** were sent. Results: `Resources/suggestion-activation-test-results.json`.
