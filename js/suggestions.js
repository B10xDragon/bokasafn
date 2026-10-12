// No account/email address required from visitors; no credentials in the frontend.
let suggestionSending = false;
function suggestionEndpoint() {
    const config = globalThis.BOKASAFN_SUGGESTIONS;
    return config?.enabled === true && /^https:\/\/formspree\.io\/f\/[a-zA-Z0-9]{6,32}$/.test(config.endpoint || '') ? config.endpoint : '';
}
function suggestionStatus(message, error = false) {
    const status = document.getElementById('suggestion-status');
    status.textContent = message;
    status.setAttribute('role', error ? 'alert' : 'status');
}
function syncSuggestionAvailability() {
    document.getElementById('suggestion-submit').disabled = suggestionSending || !suggestionEndpoint();
    if (!suggestionEndpoint()) suggestionStatus('Sending bókatillagna bíður virkjunar. Ekki er hægt að senda enn.');
}
function suggestionDraftChanged() {
    if (!suggestionSending && suggestionEndpoint()) suggestionStatus('');
}
function validateSuggestion(values) {
    const limits = {title:140, author:120, series:140, reason:2000, url:600};
    const labels = {title:'Bókatitill', author:'Höfundur', series:'Bókaflokkur', reason:'Ástæða fyrir tillögu', url:'Hlekkur á Forlagið'};
    for (const field of Object.keys(limits)) {
        if (typeof values[field] !== 'string' || values[field].length > limits[field] || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(values[field])) return {field, message:labels[field]+' er of langur eða inniheldur ógilda stafi.'};
        if (['title','author','series','url'].includes(field) && /[\r\n]/.test(values[field])) return {field, message:labels[field]+' verður að vera í einni línu.'};
    }
    if (!values.title.trim()) return {field:'title', message:'Vinsamlegast skrifaðu bókatitil.'};
    if (!values.author.trim()) return {field:'author', message:'Vinsamlegast skrifaðu nafn höfundar.'};
    if (values.url.trim()) {
        try {
            const url = new URL(values.url.trim());
            if (url.protocol !== 'https:' || !['forlagid.is','www.forlagid.is'].includes(url.hostname) || url.username || url.password || url.port || !url.pathname.startsWith('/vara/') || !url.pathname.slice(6) || url.hash) throw new Error('url');
        } catch { return {field:'url', message:'Hlekkurinn þarf að vera HTTPS-bókasíða á forlagid.is, t.d. https://www.forlagid.is/vara/bokatitill/.'}; }
    }
    return null;
}
function suggestionPayload(values) {
    const body = ['Bókatitill: '+values.title, 'Höfundur: '+values.author];
    if (values.series) body.push('Bókaflokkur: '+values.series);
    if (values.reason) body.push('Ástæða fyrir tillögu:\n'+values.reason);
    if (values.url) body.push('Hlekkur á Forlagið: '+values.url);
    return {subject:'Bókasafn — Ný bókatillaga: '+values.title, 'Bókatitill':values.title, 'Höfundur':values.author,
        ...(values.series ? {'Bókaflokkur':values.series} : {}), ...(values.reason ? {'Ástæða fyrir tillögu':values.reason} : {}),
        ...(values.url ? {'Hlekkur á Forlagið':values.url} : {}), message:body.join('\n\n'), _gotcha:''};
}
function formspreeAccepted(status, result) {
    return status >= 200 && status < 300 && result !== null && typeof result === 'object'
        && !Array.isArray(result) && !('error' in result) && !('errors' in result)
        && result.ok !== false && (result.ok === true || (typeof result.next === 'string' && result.next.length > 0));
}
function formspreeFeedback(status, result) {
    if (status === 429) return {message:'Of margar sendingar. Bíddu aðeins og reyndu aftur.'};
    const names = {'Bókatitill':'title',title:'title','Höfundur':'author',author:'author','Bókaflokkur':'series',series:'series','Ástæða fyrir tillögu':'reason',reason:'reason','Hlekkur á Forlagið':'url',url:'url'};
    const labels = {title:'bókatitilinn',author:'nafn höfundar',series:'bókaflokkinn',reason:'ástæðuna fyrir tillögunni',url:'hlekkinn á Forlagið'};
    if ([400,422].includes(status) && Array.isArray(result?.errors)) {
        for (const error of result.errors) {
            const field = Object.prototype.hasOwnProperty.call(names,error?.field) ? names[error.field] : null;
            if (field) return {field,message:'Vinsamlegast athugaðu '+labels[field]+' og reyndu aftur.'};
        }
    }
    if ([401,403,404].includes(status)) return {message:'Sendingar eru ekki tiltækar núna. Reyndu aftur síðar.'};
    return {message:'Ekki tókst að staðfesta sendingu. Textinn þinn er varðveittur hér; reyndu aftur síðar.'};
}
async function submitRecommendation(event) {
    event?.preventDefault();
    if (suggestionSending) return;
    const fields = {title:'rec-title', author:'rec-author', series:'rec-series', reason:'rec-ideas', url:'rec-url'};
    const values = Object.fromEntries(Object.entries(fields).map(([key,id]) => [key,document.getElementById(id).value.trim()]));
    Object.values(fields).forEach(id=>document.getElementById(id).removeAttribute('aria-invalid'));
    const invalid = validateSuggestion(values);
    if (invalid) { const input=document.getElementById(fields[invalid.field]);input.setAttribute('aria-invalid','true');suggestionStatus(invalid.message,true);input.focus();return; }
    const endpoint = suggestionEndpoint();
    if (!endpoint) { syncSuggestionAvailability();return; }
    if (document.getElementById('rec-website').value) { suggestionStatus('Ekki tókst að senda. Reyndu aftur.',true);return; }
    suggestionSending=true;
    const form=document.getElementById('suggestion-form');form.setAttribute('aria-busy','true');
    const button=document.getElementById('suggestion-submit');button.disabled=true;
    suggestionStatus('Sendi tillögu…');
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),20000);
    try {
        const response=await fetch(endpoint,{method:'POST',headers:{'Accept':'application/json','Content-Type':'application/json'},body:JSON.stringify(suggestionPayload(values)),signal:controller.signal,credentials:'omit',referrerPolicy:'strict-origin-when-cross-origin',redirect:'error'});
        const result = await response.json().catch(() => null);
        if (!formspreeAccepted(response.status,result)) {
            const feedback = formspreeFeedback(response.status,result);
            suggestionStatus(feedback.message,true);
            if (feedback.field) {
                const input=document.getElementById(fields[feedback.field]);
                input.setAttribute('aria-invalid','true');input.focus();
            }
            return;
        }
        // Service acceptance confirms receipt, not final delivery to the mailbox.
        suggestionStatus('Tillagan þín hefur verið send!');
        // Keep the submitted draft visible. Never store visitors’ drafts in browser storage.
    } catch (error) {
        suggestionStatus(formspreeFeedback(0,null).message,true);
    } finally {
        clearTimeout(timeout);suggestionSending=false;form.setAttribute('aria-busy','false');syncSuggestionAvailability();
    }
}
