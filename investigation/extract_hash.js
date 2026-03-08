const fs = require('fs');
const crypto = require('crypto');

// Read the bundle
const bundle = fs.readFileSync('data/debug_bundle.js', 'utf-8');

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

// Print the document in GraphQL format
function printType(type) {
    if (type.kind === 'NonNullType') return printType(type.type) + '!';
    if (type.kind === 'ListType') return '[' + printType(type.type) + ']';
    if (type.kind === 'NamedType') return type.name.value;
    return '';
}

function printValue(val) {
    if (!val) return '';
    if (val.kind === 'Variable') return '$' + val.name.value;
    if (val.kind === 'StringValue') return '"' + val.value + '"';
    if (val.kind === 'IntValue') return val.value;
    if (val.kind === 'FloatValue') return val.value;
    if (val.kind === 'BooleanValue') return String(val.value);
    if (val.kind === 'NullValue') return 'null';
    if (val.kind === 'EnumValue') return val.value;
    if (val.kind === 'ListValue') return '[' + val.values.map(printValue).join(', ') + ']';
    if (val.kind === 'ObjectValue') return '{' + val.fields.map(f => f.name.value + ': ' + printValue(f.value)).join(', ') + '}';
    return '';
}

function printArg(arg) {
    return arg.name.value + ': ' + printValue(arg.value);
}

function printDirectives(directives) {
    if (!directives || !directives.length) return '';
    return ' ' + directives.map(d => {
        let s = '@' + d.name.value;
        if (d.arguments && d.arguments.length) s += '(' + d.arguments.map(printArg).join(', ') + ')';
        return s;
    }).join(' ');
}

function printField(field, indent) {
    let s = indent;
    if (field.alias) s += field.alias.value + ': ';
    s += field.name.value;
    if (field.arguments && field.arguments.length > 0) {
        s += '(' + field.arguments.map(printArg).join(', ') + ')';
    }
    s += printDirectives(field.directives);
    if (field.selectionSet) {
        s += ' ' + printSelectionSet(field.selectionSet, indent);
    }
    return s;
}

function printSelection(sel, indent) {
    if (sel.kind === 'Field') return printField(sel, indent);
    if (sel.kind === 'FragmentSpread') return indent + '...' + sel.name.value + printDirectives(sel.directives);
    if (sel.kind === 'InlineFragment') {
        let s = indent + '...';
        if (sel.typeCondition) s += ' on ' + sel.typeCondition.name.value;
        s += printDirectives(sel.directives);
        s += ' ' + printSelectionSet(sel.selectionSet, indent);
        return s;
    }
    return '';
}

function printSelectionSet(ss, indent) {
    const inner = indent + '  ';
    return '{\n' + ss.selections.map(s => printSelection(s, inner)).join('\n') + '\n' + indent + '}';
}

function printVarDef(vd) {
    let s = '$' + vd.variable.name.value + ': ' + printType(vd.type);
    if (vd.defaultValue) s += ' = ' + printValue(vd.defaultValue);
    return s;
}

function printOperation(op) {
    let s = op.operation + ' ' + op.name.value;
    if (op.variableDefinitions && op.variableDefinitions.length > 0) {
        s += '(' + op.variableDefinitions.map(printVarDef).join(', ') + ')';
    }
    s += ' ' + printSelectionSet(op.selectionSet, '');
    return s;
}

function printFragment(frag) {
    return 'fragment ' + frag.name.value + ' on ' + frag.typeCondition.name.value + printDirectives(frag.directives) + ' ' + printSelectionSet(frag.selectionSet, '');
}

function printDoc(doc) {
    return doc.definitions.map(def => {
        if (def.kind === 'OperationDefinition') return printOperation(def);
        if (def.kind === 'FragmentDefinition') return printFragment(def);
        return '';
    }).join('\n\n');
}

const queryStr = printDoc(doc);
console.log('\n--- Query string (first 1000 chars) ---');
console.log(queryStr.slice(0, 1000));

const hash = crypto.createHash('sha256').update(queryStr).digest('hex');
console.log('\nSHA-256 hash:', hash);

// Save the query string
fs.writeFileSync('data/category_page_list_query.graphql', queryStr);
console.log('Saved to data/category_page_list_query.graphql');
