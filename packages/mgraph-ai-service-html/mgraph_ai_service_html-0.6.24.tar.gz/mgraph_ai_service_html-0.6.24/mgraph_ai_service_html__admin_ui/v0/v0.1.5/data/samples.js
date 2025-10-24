/**
 * Sample HTML Files - v0.1.5
 * Added: Micro sample for minimal testing
 */

export const Samples = {
    micro: `<html>
    <head>
        <title>an title</title>
    </head>
    <body>
        <p>A paragraph with <b>a bold</b> item</p>
    </body>
</html>`,

    simple: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Simple HTML Example</title>
</head>
<body>
    <h1>Welcome to HTML Service</h1>
    <p>This is a simple HTML document with basic elements.</p>
    
    <h2>Features</h2>
    <ul>
        <li>Parse HTML to dictionary</li>
        <li>Extract text nodes with hashes</li>
        <li>Reconstruct HTML from components</li>
    </ul>
</body>
</html>`,

    complex: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    <title>Complex HTML Document</title>
</head>
<body>
    <header class="container">
        <nav>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <article>
            <h1>Complex Nested Structure</h1>
            <section>
                <h2>Section 1</h2>
                <p>This document has <strong>deep nesting</strong> to test the parser.</p>
                <div>
                    <div>
                        <div>
                            <p>Multiple levels of <em>nested</em> content.</p>
                            <ul>
                                <li>Item 1</li>
                                <li>Item 2
                                    <ul>
                                        <li>Nested Item A</li>
                                        <li>Nested Item B</li>
                                    </ul>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>
            
            <section>
                <h2>Section 2</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Column 1</th>
                            <th>Column 2</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Data 1</td>
                            <td>Data 2</td>
                        </tr>
                    </tbody>
                </table>
            </section>
        </article>
    </main>
    
    <footer>
        <p>&copy; 2025 HTML Service</p>
    </footer>
</body>
</html>`
};