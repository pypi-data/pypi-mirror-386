from codemie_tools.base.models import ToolMetadata

COMMON_SANDBOX_LIBRARIES = [
    # Data manipulation and analysis
    "pandas",
    "numpy",
    # Plotting and visualization
    "matplotlib",
    "seaborn",
    "plotly",
    # Document processing
    "openpyxl",  # Excel files
    "xlrd",      # Legacy Excel support
    "python-docx",  # Word documents
    "python-pptx",  # PowerPoint
    "PyPDF2",    # PDF processing
    "markitdown",  # Convert various file formats to Markdown
    "pillow",    # Image processing
    # Utilities
    "tabulate",  # Pretty tables
]
READ_FILE_TOOL = ToolMetadata(
    name="read_file_from_file_system",
    description="""
    Use this tool when you need to read file from file system or disk. You are able to do that.
    """.strip(),
    label="Read file",
    user_description="""
    Allows the AI assistant to read the contents of a file from the CodeMie backed filesystem. 
    Before using it, it is necessary to add a new integration for the tool by providing:
    1. Alias (A friendly name for the filesystem access)
    2. Root directory (The base directory for file operations)
    Usage Note:
    Useful when CodeMie backend is installed locally and you need to retrieve the contents of a specific file for local development purposes.
    """.strip()
)

LIST_DIRECTORY_TOOL = ToolMetadata(
    name="list_directory_from_file_system",
    description="List files and directories in a specified folder from file system or disk",
    label="List directory",
    user_description="""
    Allows the AI assistant to view the contents of a directory in the CodeMie backed filesystem.
    Before using it, it is necessary to add a new integration for the tool by providing:
    1. Alias (A friendly name for the local filesystem access)
    2. Root directory (The base directory for file operations)
    Usage Note:
    Useful when CodeMie backend is installed locally and you need to explore the contents of a directory or locate specific files during local development.
    """.strip(),
)

WRITE_FILE_TOOL = ToolMetadata(
    name="write_file_to_file_system",
    description="""
    Use this tool when you need to create/update/write file to file system or disk. You are able to do that.
    """.strip(),
    label="Write file",
    user_description="""
    Enables the AI assistant to create or modify files in the CodeMie backed filesystem. 
    Before using it, it is necessary to add a new integration for the tool by providing:
    1. Alias (A friendly name for the filesystem access)
    2. Root directory (The base directory for file operations)
    Usage Note:
    Useful when CodeMie backend is installed locally and you need to create new files or update existing ones for local development.
    """.strip(),
)

DIFF_UPDATE_FILE_TOOL = ToolMetadata(
    name="diff_update_file_tool",
    description="""
    Use this tool when you need to update file by the provided task description
    """.strip(),
    label="Read Generate Update File (diff)",
    user_description="""
    Updates an existing file in the local filesystem. Uses a "diff" edit format, asking the Large Language Model (LLM) to specify file edits as a series of search/replace blocks. This tool is typically used to support local development activities.
    Before using it, it is necessary to add a new integration for the tool by providing:
    1. Alias (A friendly name for the local filesystem access)
    2. Root directory (The base directory for file operations on your local machine)
    Usage Note:
    Useful when CodeMie backend is installed locally and you need to make specific changes to files during local development. This tool is efficient as the model only needs to return parts of the file which have changes. It usually performs on par with "Write file" for small files and much better for large files.
    """.strip(),
)

REPLACE_STRING_TOOL = ToolMetadata(
    name="str_replace_editor",
    description="""Custom editing tool for viewing, creating and editing files
    * State is persistent across command calls and discussions with the user
    * If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
    * The `create` command cannot be used if the specified `path` already exists as a file
    * If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
    * The `undo_edit` command will revert the last edit made to the file at `path`

    Notes for using the `str_replace` command:
    * The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
    * If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
    * The `new_str` parameter should contain the edited lines that should replace the `old_str`
    """.strip(),
    label="Filesystem Editor Tool",
    user_description="""A filesystem editor tool that allows the agent to
    - view
    - create
    - navigate
    - edit files""".strip()
)

COMMAND_LINE_TOOL = ToolMetadata(
    name="run_command_line_tool",
    description="""
    Command line tool to execute CLI commands, python commands, etc.
    Can be used for invoking Git operations, running scripts, docker commands, etc. You are able to do that.
    If user asks to commit something, invoke or execute something, this tool is a good choice.
    """.strip(),
    label="Run command line",
    user_description="""
    Enables the AI assistant to execute command line operations on the local machine where CodeMie backend is installed. This tool allows for running system commands or scripts.
    Before using it, it is necessary to add a new integration for the tool by providing:
    1. Alias (A friendly name for the command line access)
    2. Root directory (The base directory for command execution)
    Usage Note:
    Useful when CodeMie backend is installed locally and you need to perform system operations or run scripts during local development.
    For safety, the tool sanitizes and blocks dangerous command patterns, including but not limited to:
    - Use of 'rm -rf' command
    - Moving files to /dev/null
    - Use of 'dd' command
    - Directly overwriting disk blocks
    - Fork bombs
    """.strip(),
)

PYTHON_RUN_CODE_TOOL = ToolMetadata(
    name="python_repl_code_interpreter",
    description="""
    A Python shell. Use this to execute python commands when you need to perform calculations, computations.
    Use this tool to generate diagrams, plots, charts and utilize available mermaid-py, matplotlib, python-mermaid libs
    Input should be a valid python command.
    """.strip(),
    label="Code Interpreter",
    user_description="""
    Provides access to a Python shell, allowing the AI assistant to execute Python commands for various computational tasks, data analysis, and visualization purposes.
    Usage Note:
    Use this tool when you need to perform calculations, computations, or generate visual representations of data. It's particularly useful for:
    - Complex mathematical operations
    - Data manipulation and analysis
    - Generating diagrams, plots, and charts
    - Creating flowcharts and diagrams using mermaid-py
    - Plotting graphs and visualizations with matplotlib
    - Utilizing python-mermaid for sequence diagrams and flowcharts
    The tool provides access to common Python libraries for these tasks.
    """.strip(),
)

GENERATE_IMAGE_TOOL = ToolMetadata(
    name="generate_image_tool",
    description="""
    Generate image tool based on user description.
    Useful when user needs to generate an image from a description.
    Uses DALL-E model to generate images.
    """,
    label="Generate image",
    user_description="""
    Enables the AI assistant to create images based on textual descriptions. This tool utilizes the DALL-E model to generate visual content from text prompts
    """.strip(),
)

CODE_EXECUTOR_TOOL = ToolMetadata(
    name="code_executor",
    description=f"""
    Execute Python code in a secure, isolated environment with file upload and export capabilities.

    CRITICAL CONSTRAINTS:
    - Python ONLY
    - ONLY use pre-installed libraries or Python standard library
    - Pre-installed libraries: {', '.join(COMMON_SANDBOX_LIBRARIES)}
    - External libraries NOT in this list are NOT available and will cause import errors
    - Code attempting to import unavailable libraries will FAIL

    FILE OPERATIONS:
    - Upload files: Provide files when creating the tool instance (passed via toolkit)
    - Uploaded files are automatically available in the working directory by their original filename
    - Export files: Use export_files parameter to download generated files after execution

    Use this tool for:
    - Running Python code safely
    - Processing uploaded files (CSV, Excel, images, etc.)
    - Data analysis and manipulation
    - Generating visualizations and charts
    - Processing documents (Excel, PDF, Word, PowerPoint)
    - Performing calculations and computations
    - Creating and exporting new files

    The code executes in isolation with resource limits and no access to external systems.
    """.strip(),
    label="Code Executor",
    user_description="""
    Execute Python code to analyze data, generate visualizations, process documents, and perform calculations.

    Key Capabilities:
    - File Upload: Upload files to the sandbox environment for processing
    - Data Analysis: Process and analyze datasets using pandas and numpy
    - Visualizations: Create charts, graphs, and plots with matplotlib, seaborn, and plotly
    - Document Processing: Work with Excel, Word, PowerPoint, and PDF files
    - Computations: Perform mathematical calculations and data transformations
    - Image Processing: Manipulate and process images
    - File Export: Export generated files for download

    Use Cases:
    - Upload CSV or Excel files and generate insights
    - Process uploaded images and create visualizations
    - Create visualizations to illustrate trends and patterns
    - Extract information from uploaded documents
    - Perform complex calculations on uploaded data
    - Transform data between different formats and export results

    Workflow:
    1. Files are automatically uploaded to sandbox if provided to the tool
    2. Execute code that processes the uploaded files (available by filename)
    3. Generate new files or visualizations
    4. Export results using export_files parameter

    The code executes securely with all files isolated in a sandbox environment.
    """.strip(),
)
