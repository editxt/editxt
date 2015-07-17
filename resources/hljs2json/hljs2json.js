/**
 * Extract HighlightJS syntax definition from language file
 *
 * Usage: node hljs2json.js HLJS_LANGUAGE_FILE
 *
 * Setup:
 *      git clone https://github.com/isagalaev/highlight.js.git hljs
 */

function exec(path, context, transform) {
    var data = fs.readFileSync(path, 'utf8');
    if (transform) {
        data = transform(data)
    }
    context = context || {};
    vm.runInNewContext(data, context, path);
    return context;
}

function loadLanguage(path, hljs) {
    return exec(path, null, function (data) {
        return data.replace(/function\s*\(hljs\)/, "function load(hljs)");
    }).load(hljs);
}

/**
 * Remove cycles from value
 *
 * Copy nested value the first time it occurs in a cycle, omit it the second.
 */
function decycle(value, parents, valueName) {
    function copy(value) {
        var omit = Array.prototype.slice.call(arguments, 1),
            obj, i, name;
        if (Object.prototype.toString.apply(value) === '[object Array]') {
            obj = [];
            for (i = 0; i < value.length; i++) {
                if (omit.indexOf(i) === -1) {
                    obj[i] = decycle(value[i], parents, i);
                }
            }
        } else {
            obj = {};
            for (name in value) {
                if (value.hasOwnProperty(name) && omit.indexOf(name) === -1) {
                    obj[name] = decycle(value[name], parents, name);
                }
            }
        }
        return obj;
    }
    if (typeof value !== 'object' || value === null || value === undefined ||
            value instanceof Boolean ||
            value instanceof Date ||
            value instanceof Number ||
            value instanceof RegExp ||
            value instanceof String ||
            Object.prototype.toString.call(value) === '[object RegExp]') {
        return value;
    }
    parents = parents || [];
    var path = parents.length ?
                    parents[parents.length - 1][1].concat([valueName]) : [],
        seen = parents.reduce(function (prev, val) {
            return val[0] === value ? [prev[0] + 1, prev[1] || val[1]] : prev;
        }, [0, null]),
        obj;
    parents = parents.concat([[value, path]]);
    if (seen[0] && value.contains) {
        return copy(value, "contains");
    } else if (seen[0] > 4) {
        console.error('omit circular (d > 10)', path);
        return undefined;
    }
    return copy(value);
}

function str(key, value) {
    if (Object.prototype.toString.call(value) === '[object RegExp]') {
        return {type: "RegExp", pattern: value.source};
    }
    return value;
}

var fs = require("fs"),
    vm = require("vm"),
    langFile = process.argv[process.argv.length - 1],
    basePath = langFile.replace(/\/languages\/[^\/]+$/, ""),
    window = {},
    lang;

exec(basePath + "/highlight.js", {"window": window});
lang = loadLanguage(langFile, window.hljs);
console.log(JSON.stringify(decycle(lang), str, 2));
