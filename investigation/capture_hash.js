const { chromium } = require('playwright');

const COOKIE_STR = `first_visit=1772913542; first_referer=; _ga=GA1.1.224203124.1772913543; ajs_anonymous_id=875fe9ec-15a5-4576-84bc-411f3fb6c30d; visitor_id=8985d4f2-adb4-4491-b6ac-f5dee479dff7; track_code=5caff0dd41; cf_clearance=pCfkP1tcaMPAScvBFzksKJXcDAC19X5An86a8sFSipQ-1772940363-1.2.1.1-96HIsCMSgAqtcHZ7rARcrqEDHqh_7Bqy5WONDz4tiziRB4SS9QJV92lZgNFcYbHwoYI6fg.IZKZwgNxoqdDjHj9iN680gdi6kx6yZ7C0WWIg02M3IHzqRVEHdIkFqO7CIDEUu00JRm3JhHyE9IuaC26dIOy0Km6c1Vv9Dd12MpWsON2GGrTvBQ6eAnWIBZ7nM76b53K9c1.ph4FsKiMXU7pzzVpX7K3HurhdLL6iH.8s_YsE3eOJnwOYyCOaTAfQ; csrf_token=1gAvFgKAt8QInujrfs2CzVTNB9DabPWsdwO2LSJbaMZYgKYDjWMgeUXoJ6c8a31o50Npuv-QrBQVhtYXUInE6A; _producthunt_session_production=ac0wCgAxryoIRlugV1pyBR%2FCxYbtleCwiXhPAf9F5Y7HyBrOeARVvSqO5hSPRTdWjVQW%2Fh5mTNO60LMMds3VwmccnIG1xeIUvrjI1obOmJQa4Udks6sGUImO3nkZAS59KinnswWXBxHOHi9ofCHlPvb0xLhohvMIjF1l3%2B0Toxj24id1oBXr6%2FeJklGub%2FqS5uVG9RYvh%2Bc4zQDaphRuFsug7HCAzl0fhQSfCpUWZNblHtwfm3Qs6f%2B1beZLJ61dmfX2%2Fg18OcYPWfqRavDlmutNEOG51%2BtDcKXXHr5fcUOKdUB%2B7ePEQllgymt6SB8ic51bXeWkGjLHpYoJVA%3D%3D--mv6O8GFHyhWl0B5s--j273tt4YZ45nDSFxEo6SyA%3D%3D`;

function parseCookies(str) {
    const cookies = [];
    str.split(';').forEach(part => {
        const [name, ...rest] = part.trim().split('=');
        if (name && rest.length > 0) {
            cookies.push({
                name: name.trim(),
                value: rest.join('=').trim(),
                domain: '.producthunt.com',
                path: '/',
            });
        }
    });
    return cookies;
}

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();

    // Set cookies
    await context.addCookies(parseCookies(COOKIE_STR));

    const page = await context.newPage();
    const gqlRequests = [];

    // Intercept all GraphQL requests
    page.on('request', request => {
        const url = request.url();
        if (url.includes('/frontend/graphql')) {
            const urlObj = new URL(url);
            const opName = urlObj.searchParams.get('operationName');
            const variables = urlObj.searchParams.get('variables');
            const extensions = urlObj.searchParams.get('extensions');

            let hash = null;
            try {
                const ext = JSON.parse(extensions || '{}');
                hash = ext?.persistedQuery?.sha256Hash;
            } catch(e) {}

            gqlRequests.push({ opName, variables, hash, url: url.slice(0, 200) });
            console.log(`[GQL] ${opName} hash=${hash}`);
        }
    });

    try {
        await page.goto('https://www.producthunt.com/categories/ai-meeting-notetakers', {
            waitUntil: 'networkidle',
            timeout: 30000,
        });
        // Wait a bit more for lazy requests
        await page.waitForTimeout(3000);
    } catch(e) {
        console.log('Navigation error (ok):', e.message);
    }

    console.log('\n=== Summary of GraphQL requests ===');
    const byOp = {};
    gqlRequests.forEach(r => {
        if (!byOp[r.opName]) byOp[r.opName] = r.hash;
    });

    Object.entries(byOp).forEach(([op, hash]) => {
        console.log(`${op}: ${hash}`);
    });

    // Save all hashes
    require('fs').writeFileSync('data/captured_hashes.json', JSON.stringify(byOp, null, 2));
    console.log('\nSaved to data/captured_hashes.json');

    await browser.close();
})();
