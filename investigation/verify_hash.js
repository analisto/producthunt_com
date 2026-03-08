const fs = require('fs');
const crypto = require('crypto');
const { print } = require('graphql');

const bundle = fs.readFileSync('data/debug_bundle.js', 'utf-8');
const KNOWN_HASH = 'eeaa942691c4ef61705f6147c8f0cc2e74beef7638f8c68fb2569fb30e020287';

function extractDoc(opName) {
    const idx = bundle.indexOf(`"${opName}"`);
    if (idx === -1) { console.log(`${opName} not found`); return null; }
    const docStart = bundle.lastIndexOf('{kind:"Document"', idx);

    let depth = 0, end = docStart;
    let inStr = false, strChar = '';
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

// Test with CategoryPageQuery
const categoryPageDoc = extractDoc('CategoryPageQuery');
if (categoryPageDoc) {
    const queryStr = print(categoryPageDoc);
    const hash = crypto.createHash('sha256').update(queryStr).digest('hex');
    console.log('CategoryPageQuery hash:', hash);
    console.log('Expected:             ', KNOWN_HASH);
    console.log('Match:', hash === KNOWN_HASH);
}

// Also compute for CategoryPageListQuery
const listDoc = extractDoc('CategoryPageListQuery');
if (listDoc) {
    const queryStr = print(listDoc);
    const hash = crypto.createHash('sha256').update(queryStr).digest('hex');
    console.log('\nCategoryPageListQuery hash:', hash);
    fs.writeFileSync('data/list_query_hash.txt', hash);
}
