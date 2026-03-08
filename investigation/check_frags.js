const fs = require('fs');
const { print } = require('graphql');
const bundle = fs.readFileSync('data/debug_bundle.js', 'utf-8');

function extractDoc(opName) {
    const idx = bundle.indexOf('"' + opName + '"');
    if (idx === -1) return null;
    const docStart = bundle.lastIndexOf('{kind:"Document"', idx);
    let depth = 0, end = docStart, inStr = false, strChar = '';
    for (let i = docStart; i < bundle.length; i++) {
        const c = bundle[i];
        if (inStr) {
            if (c === strChar && bundle[i-1] !== '\\') inStr = false;
        } else if (c === '"' || c === "'") {
            inStr = true; strChar = c;
        } else if (c === '{') depth++;
        else if (c === '}') {
            depth--;
            if (depth === 0) { end = i; break; }
        }
    }
    const docStr = bundle.slice(docStart, end + 1);
    return eval('(' + docStr.replace(/!0/g, 'true').replace(/!1/g, 'false') + ')');
}

['CategoryPageQuery', 'CategoryPageListQuery'].forEach(opName => {
    const doc = extractDoc(opName);
    if (!doc) { console.log(opName + ': not found'); return; }
    const printed = print(doc);

    const spreads = [...printed.matchAll(/\.\.\.([A-Za-z]+)/g)].map(m => m[1]);
    const defs = [...printed.matchAll(/^fragment ([A-Za-z]+)/gm)].map(m => m[1]);
    const missing = [...new Set(spreads)].filter(s => !defs.includes(s));

    console.log('\n=== ' + opName + ' ===');
    console.log('Defined fragments:', defs.length);
    console.log('Missing fragments:', missing);
});
