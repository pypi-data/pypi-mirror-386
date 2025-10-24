Read content from a file.

**Tips:**
- Make sure you follow the description of each tool parameter.
- A `<system>` tag will be given before the read file content.
- Content will be returned with a line number before each line like `cat -n` format.
- Use `line_offset` and `n_lines` parameters when you only need to read a part of the file.
- The maximum number of lines that can be read at once is ${MAX_LINES}.
- Any lines longer than ${MAX_LINE_LENGTH} characters will be truncated, ending with "...".
- The system will notify you when there is any limitation hit when reading the file.
- This tool is a tool that you typically want to use in parallel. Always read multiple files in one response when possible.
- This tool can only read text files. To list directories, you must use the Glob tool or `ls` command via the Bash tool. To read other file types, use appropriate commands via the Bash tool.
- If the file doesn't exist or path is invalid, an error will be returned.
- If you want to search for a certain content/pattern, prefer Grep tool over ReadFile.
