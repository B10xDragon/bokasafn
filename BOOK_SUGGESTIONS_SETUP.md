# Activate email-based book suggestions

## Current status

The static form and Formspree integration are implemented. **Email delivery is not active or verified.** No Formspree account, verified recipient or actual form ID was available in this session. `js/suggestion-config.js` therefore has `enabled: false` and an empty endpoint. The visitor sees an Icelandic pending-activation notice and a disabled send button. No mail app opens, no secret is committed, and the unconfigured form sends nothing.

Formspree was selected because its form-ID endpoints support GitHub Pages, JSON AJAX submissions, configurable email notifications, honeypots, domain restrictions and provider rate limits without visitor accounts or email addresses. This integration uses native `fetch`, not an added library. A form ID is public configuration; it is not an API secret.

## Exact owner setup

1. Register or sign in at [Formspree](https://formspree.io/register). Create a form named **Bókasafn — Bókatillögur**, or use the preconfigured link below. Choose `jon3107bok@gmail.com` as the notification recipient. Complete any account and recipient verification emails. Visitors do not register.
2. In the form's email notification action, confirm that notifications are enabled and delivered to that recipient. Use the submitted `subject` field for the email subject, rather than overriding it with a fixed dashboard subject. The form supplies `Bókasafn — Ný bókatillaga: [title]`. Keep the standard notification fields and `message` visible; all supplied optional details appear in the readable message too.
3. Add server-side field validation in the dashboard/claim form where available: `Bókatitill` required/max 140, `Höfundur` required/max 120, `Bókaflokkur` optional/max 140, `Ástæða fyrir tillögu` optional/max 2000, `Hlekkur á Forlagið` optional/max 600. Do **not** require an `email` field. Frontend limits improve usability; they are not a substitute for provider protections against direct requests.
4. In **Project → Settings → Restrict to Domain**, enter the actual deployed hostname, normally `b10xdragon.github.io`, without `https://` or `/bokasafn`. If GitHub Pages uses a custom domain, use that hostname instead. Confirm the hostname from the actual Pages deployment. Localhost submissions will not be accepted after this restriction is enabled; use the deployed site for the real test. The request sends an origin referrer as required by Formspree's documented domain check.
5. Keep Formspree's automatic spam filtering and the form's `_gotcha` honeypot. Formspree documents a **20 posts/minute/form** system rate limit and plan-based monthly quotas; choose a plan appropriate to expected use and monitor submissions/spam. Domain restrictions are an additional spam signal, not authentication. The fixed recipient is configured at the provider; the frontend cannot choose arbitrary recipients.
6. Under **Form → Settings → Spam protection**, ensure the ordinary JSON AJAX endpoint works without an interactive CAPTCHA redirect. This implementation does not render a CAPTCHA widget. If reCAPTCHA is enabled, disable that interactive challenge for this form, keeping the other protections above. Alternatively leave activation pending until a separately configured on-page CAPTCHA integration is added. Never put a CAPTCHA secret or Gmail password in the repository. See the provider's [reCAPTCHA settings](https://help.formspree.io/articles/form-and-project-settings/recaptcha-settings/).
7. Copy the real endpoint from **Integration**, e.g. `https://formspree.io/f/abcdefgh`, into `js/suggestion-config.js`:

   ```js
   globalThis.BOKASAFN_SUGGESTIONS = {
       enabled: true,
       endpoint: 'https://formspree.io/f/YOUR_ACTUAL_FORM_ID'
   };
   ```

   Replace the entire placeholder with the provider's real form ID. Only HTTPS form-ID URLs on `formspree.io` are accepted. Do not paste a Gmail address, account API token or secret. Change the config script's cache-version query in `index.html` when activating, commit and push **Beta only**. Confirm which branch GitHub Pages actually publishes before expecting that deployment to change; do not merge into main as part of this task.
8. From the deployed site, submit one clearly labelled test suggestion such as **Prófun — Bókasafn** with a real author and optional series/reason/Forlagið product link. Confirm the browser reports acceptance, the submission appears in Formspree's inbox, and the email actually reaches `jon3107bok@gmail.com` with the exact subject and all provided details. Check Gmail spam too. Provider acceptance alone does not prove final mailbox delivery.
9. If the real test fails, set `enabled: false`, publish that configuration and resolve recipient verification, notification settings, CAPTCHA, quota or domain restrictions. Do not label email delivery operational until step 8 succeeds. Never load-test the public provider endpoint.
10. Review/delete old submissions periodically in the provider dashboard according to school privacy requirements. The site does not collect visitor email addresses or persist suggestion drafts in browser storage. Formspree processes submission text and normal request metadata; its own privacy policy applies. Visitors are asked not to include personal information.

### Optional preconfigured form creation

[Create/claim the Bókasafn form](https://formspree.io/claim?name=B%C3%B3kasafn%20%E2%80%94%20B%C3%B3katill%C3%B6gur&project=bokasafn&field.B%C3%B3katitill=text%2Crequired%2Cmaxlength%3A140&field.H%C3%B6fundur=text%2Crequired%2Cmaxlength%3A120&field.B%C3%B3kaflokkur=text%2Cmaxlength%3A140&field.%C3%81st%C3%A6%C3%B0a%20fyrir%20till%C3%B6gu=text%2Cmaxlength%3A2000&field.Hlekkur%20%C3%A1%20Forlagi%C3%B0=url%2Cmaxlength%3A600&action.email=jon3107bok%40gmail.com)

This provider-supported claim URL opens registration/confirmation; it does not silently create an account or send an email from this repository. Verify all dashboard settings above after claiming.

## Verified documentation and test limits

Provider documentation inspected on 2026-10-12:

- [Static integration and claim URL syntax](https://formspree.io/llms.txt)
- [AJAX submissions](https://help.formspree.io/articles/building-your-form/submit-forms-with-javascript-ajax/)
- [Email subject field](https://help.formspree.io/articles/building-your-form/email-subject-line/): `subject`, available on all plans.
- [Honeypot](https://help.formspree.io/articles/building-your-form/honeypot-spam-filtering/): `_gotcha`.
- [Domain restrictions](https://help.formspree.io/articles/form-and-project-settings/restrict-to-domain/)
- [Spam protection](https://help.formspree.io/articles/troubleshooting/how-to-prevent-spam/)
- [System and AJAX rate limits](https://help.formspree.io/articles/form-and-project-settings/system-limits/)
- The published [Formspree AJAX client](https://unpkg.com/@formspree/ajax@1), using core v4, recognises a JSON `next` string as success and an `error`/`errors` field as failure. Our native integration additionally requires an HTTP success status and never follows the returned URL.

Automated tests intercept a test form-ID URL and simulate this documented response format, network failure, 500, 429 and unexpected bodies. These tests exercise the browser integration without transmitting visitor data or emails. **They are not an end-to-end provider/mailbox test.** That supported activation test is step 8 and remains pending until the owner configures the account and verified endpoint.
