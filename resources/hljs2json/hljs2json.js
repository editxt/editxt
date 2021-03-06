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
        return data.replace(/function(\s+\w*)?\s*\(hljs\)/, "function load(hljs)");
    }).load(hljs);
}

/**
 * Replace cycles in value with RecursiveRef objects
 */
function decycle(value, path, seen) {
    if (isSimple(value)) {
        return value;
    }
    var i, name, pair, copy;
    if (!seen) {
        seen = [];
        path = [];
    } else if (path[path.length - 1] === "contains" ||
               path[path.length - 2] === "contains") {
        for (i = seen.length - 1; i >= 0; i--) {
            pair = seen[i];
            if (pair[0] === value) {
                return recursiveRef(pair[1], value, path)
            }
        }
    }
    seen.push([value, path]);
    if (Object.prototype.toString.apply(value) === '[object Array]') {
        copy = [];
        for (i = 0; i < value.length; i++) {
            copy.push(decycle(value[i], path.concat([i]), seen));
        }
    } else {
        copy = {};
        for (name in value) {
            if (value.hasOwnProperty(name)) {
                copy[name] = decycle(value[name], path.concat([name]), seen);
            }
        }
    }
    return copy;
}

function str(key, value) {
    if (Object.prototype.toString.call(value) === '[object RegExp]') {
        return {type: "RegExp", pattern: value.source};
    }
    return value;
}

function isSimple(value) {
    return typeof value !== 'object' || value === null || value === undefined ||
            value instanceof Boolean ||
            value instanceof Date ||
            value instanceof Number ||
            value instanceof RegExp ||
            value instanceof String ||
            Object.prototype.toString.call(value) === '[object RegExp]';
}

function recursiveRef(path, value, thisPath) {
    var desc = {};
    if (Object.prototype.toString.apply(value) === '[object Array]') {
        desc = thisPath.join("-");
    } else {
        for (key in value) {
            if (value.hasOwnProperty(key)) {
                desc[key] = isSimple(value[key]) ? value[key] : "...";
            }
        }
    }
    return {type: "RecursiveRef", path: path, desc: desc}
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
