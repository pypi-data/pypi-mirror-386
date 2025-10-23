# How-to: Use the Parser App

This how-to guide explains how to use the Parser App in your browser to upload files, run the parser, and transfer parsed metadata to the Data Store. It is intended for users who want a step-by-step walkthrough of the main app functions.

!!! note "Prerequisites"
    <!-- List here any prerequisites needed to deploy or understand the app (e.g., login credentials, access to Spaces, supported file formats). -->
    **WIP**

---

## Open and login in the app

<ol>
    <li>Open your web browser.</li>
    <li>Go to the provided URL of the Parser App (e.g., https://parser.example.com).</li>
    <li>The login page of the app will appear.</li>

    <div class="click-zoom">
        <label>
            <input type="checkbox">
            <img src="../../../assets/parsing/LoginParserApp.jpg" alt="Login in the Parser App." width="50%" title="Click to zoom in">
        </label>
    </div>

    <li>Enter your Username.</li>
    <li>Enter your Password.</li>
    <li>Press <b>Login</b>.</li>
</ol>


## Select and Upload Files
1. Select the Space where data will be saved.
2. Enter Project and Collection names.
3. Drag and drop or click to select files.
4. Press **Upload Files** to upload them.
    - Click the **Reset** button to start over if needed.

<div class="click-zoom">
    <label>
        <input type="checkbox">
        <img src="../../../assets/parsing/Card1ParserApp.jpg" alt="Card 1 in the Parser App." width="50%" title="Click to zoom in">
    </label>
</div>


## Select Parsers
1. Choose a parser by clicking **Select Parser** for each uploaded file.
    - Available parsers are listed in the corner.
    - See [How-to: Create new parsers](create_new_parsers.md) to create your own.
2. Press **Parse** to extract metadata from each file and upload it to the Data Store. The extraction is defined in the logic of each defined parser.

<div class="click-zoom">
    <label>
        <input type="checkbox">
        <img src="../../../assets/parsing/Card2.jpg" alt="Card 2 in the Parser App." width="50%" title="Click to zoom in">
    </label>
</div>

## Review Logs
1. Check logs to verify successful parsing. If parsing fails, check the logs and debug the parsing process.
2. If parsing works, only INFO messages will appear in the logs card.
3. The logs will show whether objects were created new or updated if they already existed in the Data Store.

<div class="click-zoom">
    <label>
        <input type="checkbox">
        <img src="../../../assets/parsing/Card3Logs.jpg" alt="Card 3 in the Parser App." width="50%" title="Click to zoom in">
    </label>
</div>

---

## Advanced: Updating Existing Objects

The Parser App can update existing objects in the Data Store rather than always creating new ones. This is useful when you want to:

- Update metadata for samples or experiments that already exist.
- Correct or enrich existing data.
- Maintain consistent object codes across multiple parsing operations.

To update an existing object, your parser must set the `code` attribute on the object instance. When the `code` is set:

1. The Parser App looks for an existing object with that code in your Space/Project/Collection (note that Collection is optional if objects exist at the Project level).
2. If found, the object's properties are updated with the new values.
3. A log message confirms that the existing object was updated.

!!! warning
    Note that the object must exist in the specified Space, Project, and, optionally, Collection names.

See [How-to: Create new parsers](create_new_parsers.md#referencing-existing-objects-in-openbis) for details on implementing this in custom parsers.
