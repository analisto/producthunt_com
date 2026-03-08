const fs = require('fs');
const crypto = require('crypto');
const { print, parse } = require('graphql');

// Read the bundle
// Drop the downloaded JS bundle here before running: scripts/debug_bundle.js
const bundle = fs.readFileSync('scripts/debug_bundle.js', 'utf-8');

// Find CategoryPageListQuery document object
const idx = bundle.indexOf('"CategoryPageListQuery"');
const docStart = bundle.lastIndexOf('{kind:"Document"', idx);

// Extract the JS object by counting braces
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
console.log('Extracted doc length:', docStr.length);

// Evaluate the JS object
let doc;
try {
    doc = eval('(' + docStr.replace(/!0/g, 'true').replace(/!1/g, 'false') + ')');
    console.log('Eval succeeded!');
} catch(e) {
    console.log('Eval failed:', e.message);
    process.exit(1);
}

// Use graphql-js print function for canonical output
const queryStr = print(doc);
console.log('\n--- Query string (first 1000 chars) ---');
console.log(queryStr.slice(0, 1000));

const hash = crypto.createHash('sha256').update(queryStr).digest('hex');
console.log('\nSHA-256 hash:', hash);

fs.writeFileSync('scripts/category_page_list_query.graphql', queryStr);
console.log('Saved to scripts/category_page_list_query.graphql');
